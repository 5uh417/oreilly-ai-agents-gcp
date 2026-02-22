# @summary Manages firewall rules for the web application
#
# @param port The port to open
# @param allowed_ips List of IPs to allow
#
class webapp::firewall (
  $port        = undef,
  $allowed_ips = [],
) {

  # ---- PUPPET 7 ANTI-PATTERN: Legacy facts ----
  $my_ip = $::ipaddress

  # ---- PUPPET 7 ANTI-PATTERN: validate_* functions ----
  validate_array($allowed_ips)

  if is_ip_address($my_ip) {
    notice("Configuring firewall for server IP: ${my_ip}")
  }

  # ---- PUPPET 7 ANTI-PATTERN: Legacy fact in conditional ----
  case $::osfamily {
    'RedHat': {
      $firewall_provider = 'iptables'
    }
    'Debian': {
      $firewall_provider = 'iptables'
    }
    default: {
      fail("Unsupported OS family for firewall: ${::osfamily}")
    }
  }

  # Open the application port
  firewall { "100 allow webapp port ${port}":
    dport  => $port,
    proto  => 'tcp',
    action => 'accept',
  }

  # Allow access from specific IPs
  $allowed_ips.each |$index, $ip| {
    if is_ipv4_address($ip) {
      firewall { "200 allow access from ${ip}":
        source => $ip,
        dport  => $port,
        proto  => 'tcp',
        action => 'accept',
      }
    }
  }
}
