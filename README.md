# check_metric_value
Nagios/Icinga module to check Prometheus exporter metrics

# Icinga2 Command definition
~~~
object CheckCommand "check_metric_value" {
  import "plugin-check-command"

  command = [ "/opt/check_metric_value/check_metric_value.py" ] 

  arguments = {
    "-P" = "/root/go/bin/prom2json"
    "-U" = "$metric_url$"
    "-M" = "$metric_name$"
    "-o" = "$metric_operator$"
    "-w" = "$metric_warn$"
    "-c" = "$metric_crit$"
    "-n" = {
      set_if = "$metric_labelname$"
      value = "$metric_labelname$"
    }
    "-v" = {
      set_if = "$metric_labelvalue$"
      value = "$metric_labelvalue$"
    }
    "-u" = {
      set_if = "$metric_unit$"
      value = "$metric_unit$"
    }

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
