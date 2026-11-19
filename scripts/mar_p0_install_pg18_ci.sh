#!/usr/bin/env bash
# Install PostgreSQL 18 on the tested Ubuntu 26.04 runner from signed PGDG.
set -euo pipefail
if [[ $# -ne 1 ]] || [[ "$1" != "client" && "$1" != "server" ]]; then
  echo "Expected client or server" >&2
  exit 2
fi
source /etc/os-release
test "$VERSION_ID" = "26.04" || { echo "Ubuntu 26.04 is required" >&2; exit 2; }
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ca-certificates curl gpg
sudo install -d -m 0755 /usr/share/postgresql-common/pgdg
sudo curl --fail --silent --show-error --location --retry 3 \
  -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
  https://www.postgresql.org/media/keys/ACCC4CF8.asc
pgdg_fingerprint="$(gpg --batch --show-keys --with-colons \
  /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
  | awk -F: '$1 == "fpr" { print $10; exit }')"
test "$pgdg_fingerprint" = "B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8" \
  || { echo "Unrecognized PostgreSQL signing key" >&2; exit 2; }
printf 'Types: deb\nURIs: https://apt.postgresql.org/pub/repos/apt\nSuites: %s-pgdg\nComponents: main\nSigned-By: /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc\n' \
  "$VERSION_CODENAME" | sudo tee /etc/apt/sources.list.d/pgdg.sources >/dev/null
sudo apt-get update -qq
if [[ "$1" == "server" ]]; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    postgresql-18 postgresql-client-18
  sudo service postgresql start
else
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    postgresql-client-18
fi
pg_dump --version
psql --version
