# @summary Handles application deployment from artifact repository
#
# @param version The version to deploy
# @param artifact_url The base URL for artifacts
# @param checksum The expected checksum
# @param restart_on_deploy Whether to restart on deploy
#
define webapp::deploy (
  $version           = 'latest',
  $artifact_url      = undef,
  $checksum          = undef,
  $restart_on_deploy = true,
) {

  # ---- PUPPET 7 ANTI-PATTERN: validate_* functions ----
  validate_string($version)
  validate_bool($restart_on_deploy)

  if $artifact_url != undef {
    validate_string($artifact_url)
  }

  # ---- PUPPET 7 ANTI-PATTERN: Legacy facts ----
  $hostname    = $::hostname
  $environment = $::environment

  # ---- PUPPET 7 ANTI-PATTERN: Deprecated stdlib functions ----
  $version_upper = upcase($version)
  $clean_name    = strip($name)
  $deploy_tag    = downcase("${hostname}-${version}")

  # ---- PUPPET 7 ANTI-PATTERN: Implicit type coercion ----
  $deploy_timestamp = "deployed_at_${::uptime_seconds}"

  # ---- PUPPET 7 ANTI-PATTERN: hiera() in define ----
  $deploy_settings = hiera('webapp::deploy_settings', {})

  # ---- PUPPET 7 ANTI-PATTERN: has_key() ----
  if has_key($deploy_settings, 'timeout') {
    $timeout = $deploy_settings['timeout']
  } else {
    $timeout = 300
  }

  $deploy_dir = "/opt/webapp/releases/${clean_name}-${version}"

  file { $deploy_dir:
    ensure => directory,
    owner  => 'webapp',
    group  => 'webapp',
    mode   => '0755',
  }

  if $artifact_url {
    exec { "download-${name}-${version}":
      command => "/usr/bin/curl -sL ${artifact_url}/${name}-${version}.tar.gz -o /tmp/${name}-${version}.tar.gz",
      creates => "/tmp/${name}-${version}.tar.gz",
      timeout => $timeout,
    }

    exec { "extract-${name}-${version}":
      command => "/bin/tar xzf /tmp/${name}-${version}.tar.gz -C ${deploy_dir}",
      require => [
        Exec["download-${name}-${version}"],
        File[$deploy_dir],
      ],
      creates => "${deploy_dir}/app.jar",
    }
  }

  file { "${deploy_dir}/deploy.info":
    ensure  => file,
    owner   => 'webapp',
    group   => 'webapp',
    mode    => '0644',
    content => "version=${version}\nhost=${hostname}\ntag=${deploy_tag}\ntime=${deploy_timestamp}\n",
  }
}
