#!/usr/bin/python3

import argparse
import datetime
import json
import subprocess
import sys


def exit_ok(message):
  """
  Beenden mit Rueckgabe OK im Format fuer Nagios/Icinga
  """
  print(f"OK - {message}")
  sys.exit(0)


def exit_warning(message):
  """
  Beenden mit Rueckgabe WARNING im Format fuer Nagios/Icinga
  """
  print(f"WARNING - {message}")
  sys.exit(1)


def exit_critical(message):
  """
  Beenden mit Rueckgabe CRITICAL im Format fuer Nagios/Icinga
  """
  print(f"CRITICAL - {message}")
  sys.exit(2)


def exit_unknown(message):
  """
  Beenden mit Rueckgabe UNKNOWN im Format fuer Nagios/Icinga
  """
  print(f"UNKNOWN - {message}")
  sys.exit(3)




def parse_arguments():
  """
  Definition und Parsen der Kommandozeilenargumente
  """
  parser = argparse.ArgumentParser(description='Nagios/Icinga plugin for Prometheus metric values')

  parser.add_argument('-D', '--debug', default=False, help="enable Debug output", action='store_true', dest='debug')
  parser.add_argument('-P', '--prom2json', required=False, help="prom2json executable", dest='prom2json', default='prom2json')
  parser.add_argument('-U', '--url', required=True, help="Metrics URL, ex. http://localhost/metrics", dest='url')
  parser.add_argument('-M', '--metric', required=True, help="metric name", dest='metric')

  parser.add_argument('-n', '--label-name', required=False, help="label name to match", dest='label_name', default='Not set')
  parser.add_argument('-v', '--label-value', required=False, help="label value to match", dest='label_value', default='Not set')

  parser.add_argument('-o', '--operator', required=True, help="operator", dest='operator', choices=['gt','lt','gt-date','lt-date'])
  parser.add_argument('-u', '--unit', required=False, help="unit for date compare", dest='unit', choices=['days','hours','minutes'], default='days')
  parser.add_argument('-w', '--warning', required=True, help="warning value", dest='warning', type=int)
  parser.add_argument('-c', '--critical', required=True, help="critical value", dest='critical', type=int)

  return parser.parse_args()



def process_json(args, json_raw):
  """
  Verarbeitung des geparsten JSON und suchen der Metrik
  """
  if args.debug:
     print(f"DEBUG: [process_json] count = {len(json_raw)}, metric = {args.metric} ")

  for metric in json_raw:
    if metric['name'] == args.metric:

      if args.debug:
        print(f"DEBUG: [process_json] metric found, raw = {metric}")


      if len(metric['metrics']) < 1:
        exit_unknown(f"Metric contains no metrics -- {metric}")

      elif len(metric['metrics']) == 1:
        process_metric(args, metric, metric['metrics'][0])

      else:
        if args.debug:
          print(f"DEBUG: [process_json] metric contain multiple values, label_name = {args.label_name}, label_value = {args.label_value}")

        for metric_value in metric['metrics']:
          if args.label_name == 'Not set' or args.label_value == 'Not set':
            exit_unknown(f"-n/--label-name and -v/--label-value are required for multi-value metrics -- {metric}")

          if metric_value['labels'][args.label_name] == args.label_value:
            process_metric(args, metric, metric_value)


      exit_unknown(f"No metric found with label_name = {args.label_name}, label_value = {args.label_value} -- {metric}")


  exit_unknown(f"Metric with name = {args.metric} not found")



def process_metric(args, metric, metric_value):
  """
  Verarbeitung einer gefundenen Metrik und Pruefung des Typs
  """
  if args.debug:
     print(f"DEBUG: [process_metric] metric_value = {metric_value}, metric = {metric} ")

  metric_type = metric['type']

  if args.debug:
    print(f"DEBUG: [process_json] metric type, raw = {metric_type}")

  if metric_type == "COUNTER" or metric_type == "GAUGE" or metric_type == "UNTYPED" :
      process_metric_value(args, metric, metric_value)

  elif metric_type == "HISTOGRAMM":
      exit_unknown(f"Unsupported Metric type: {metric_type}")

  elif metric_type == "SUMMARY":
    exit_unknown(f"Unsupported Metric type: {metric_type}")

  else:
    exit_unknown(f"Unsupported Metric type: {metric_type}")



def process_metric_value(args, metric, metric_value):
  """
  Verarbeitung eines konkreten Metrik-Wertes und Auswertung der Vergleichs-Operatoren
  """
  if args.debug:
    print(f"DEBUG: [process_metric_value] operator = {args.operator}, warning = {args.warning}, critical = {args.critical}, metric_value = {metric_value}, metric = {metric}")

  if args.operator == 'gt' or args.operator == 'lt':
    process_metric_value_number(args, metric, metric_value)

  elif args.operator == 'gt-date' or args.operator == 'lt-date':
    process_metric_value_date(args, metric, metric_value)

  else:
    exit_unknown(f"Unsupported operator: {args.operator}")



def process_metric_value_number(args, metric, metric_value):
  """
  Auswertung eines Metrik-Wertes mit numerischen Vergleich
  """
  if args.debug:
    print(f"DEBUG: [process_metric_value_number] operator = {args.operator}, warning = {args.warning}, critical = {args.critical}, metric_value = {metric_value}, metric = {metric}")

  try:
    value = float(metric_value['value'])

  except Exception as err:
     exit_unknown(f"DEBUG: [process_metric_value] error getting metric value as float, metric_value = {metric_value}, metric = {metric} -- {err}")

  if args.debug:
    print(f"DEBUG: [process_metric_value_number] Parsed value(float) = {value}")

  if args.operator == 'gt':

    if value > args.critical:
      exit_critical(f"value = {value}")

    elif value > args.warning:
      exit_warning(f"value = {value}")

    else:
      exit_ok(f"value = {value}")

  elif args.operator == 'lt':

    if value < args.critical:
      exit_critical(f"value = {value}")

    elif value < args.warning:
      exit_warning(f"value = {value}")

    else:
      exit_ok(f"value = {value}")



def process_metric_value_date(args, metric, metric_value):
  """
  Auswertung eines Metrik-Wertes mit Vergleich fuer Timestamp
  """
  if args.debug:
    print(f"DEBUG: [process_metric_value_date] operator = {args.operator}, unit = {args.unit}, warning = {args.warning}, critical = {args.critical}, metric_value = {metric_value}, metric = {metric}")

  try:
    value = float(metric_value['value'])
    dt = datetime.datetime.fromtimestamp(value)

  except Exception as err:
     exit_unknown(f"DEBUG: [process_metric_value_date] error getting metric value as float, metric_value = {metric_value}, metric = {metric} -- {err}")

  if args.debug:
    print(f"DEBUG: [process_metric_value_date] Parsed value(datetime) = {dt}")

  if args.unit == 'days':
    warn = datetime.timedelta(days=args.warning)
    crit = datetime.timedelta(days=args.critical)
  elif args.unit == 'hours':
    warn = datetime.timedelta(hours=args.warning)
    crit = datetime.timedelta(hours=args.critical)
  elif args.unit == 'minutes':
    warn = datetime.timedelta(minutes=args.warning)
    crit = datetime.timedelta(minutes=args.critical)
  else:
    exit_unknown(f"DEBUG: [process_metric_value_date] invalid date compare unit: {args.unit}")


  if args.operator == 'gt-date':

    if dt + crit > datetime.datetime.now():
      exit_critical(f"value = {value}")

    elif dt + warn > datetime.datetime.now():
      exit_warning(f"value = {value}")

    else:
      exit_ok(f"value = {value}")

  elif args.operator == 'lt-date':

    if dt + crit < datetime.datetime.now():
      exit_critical(f"value = {value}")

    elif dt + warn < datetime.datetime.now():
      exit_warning(f"value = {value}")

    else:
      exit_ok(f"value = {value}")



# main #########################################################################

try:
  args = parse_arguments()

except Exception as err:
  exit_unknown(f"Error in Argument parse -- {err}")

if args.debug:
  print(f"DEBUG: Prom2JSON Executable = {args.prom2json}, Url = {args.url}")

try:
  process = subprocess.run(f"{args.prom2json} {args.url}", capture_output=True, shell=True, universal_newlines=True)

except Exception as err:
  exit_unknown(f"Error running subprocess -- {err}")

if args.debug:
  print(f"DEBUG: Returncode = {process.returncode}")

if process.returncode < 0:
  exit_unknown(f"Error running subprocess, reurncode = {process.retuncode}, output = {process.stderr} {process.stdout}")

try:
  json_raw = json.loads(process.stdout)

except Exception as err:
  exit_unknown(f"Error parsing JSON -- {err}")

process_json(args, json_raw)

exit_unknown(f"Unknown error, process did not exit")







