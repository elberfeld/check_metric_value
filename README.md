# check_metric_value
Nagios/Icinga module to check Prometheus exporter metrics
Uses: https://github.com/prometheus/prom2json

# Icinga2 Command definition
~~~
object CheckCommand "check_metric_value" {
  import "plugin-check-command"

  command = [ "/opt/check_metric_value/check_metric_value.py" ] 

  arguments = {
    "-P" = "/opt/bin/prom2json"
    "-U" = "$metric_url$"
    "-M" = "$metric_name$"
    "-n" = "$metric_labelname$"
    "-v" = "$metric_labelvalue$"
    "-o" = "$metric_operator$"
    "-u" = "$metric_unit$"
    "-w" = "$metric_warn$"
    "-c" = "$metric_crit$"
  }
}
~~~
# Sample Icinga2 Service 
~~~
apply Service "node_reboot_required" {
  import "generic-service"

  check_command = "check_metric_value"
  enable_perfdata = false

  vars.metric_url = "http://{{int_ip4}}:9100/metrics"
  vars.metric_name = "node_reboot_required"
  vars.metric_operator = "gt"
  vars.metric_warn = "0"
  vars.metric_crit = "1"

  assign where host.name == "{{host}}" host.vars.os == "Linux"
}
~~~
