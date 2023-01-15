# ldap-passwd-webui

This project is a fork of [ldap-passwd-webui](https://github.com/jirutka/ldap-passwd-webui)
from [jirutka](https://github.com/jirutka) with a lot of changes.

## Changes made in contrast to the original project

1. The initial search for the userid is done by a qualified user, the `search_user`.
2. The app only works for one LDAP-Server, support for password change on multiple LDAP server and AD was removed.
3. Every connection to the LDAP-Server ist encrypted using STARTLS over the standardized tcp port 389 for ldap. The
   possibility to connect via tcp/636 was removed, because it is deprecated. An alternative port can be configured
   via `port`-parameter in [settings.ini](settings.ini.example).
4. You must provide a x509v3 root certificate to the app (`ca_cert` in [setting.ini](settings.ini.example). The server
   certificate is verified against this root certificate.
5. A password validator was implemented, it checks for weak and trivial passphrases. Optionally you can add wordlists to
   the [wordlists](wordlists/README.md) directory, any new password must not be part of these lists.

## Requirements

* Python3  >= 3.9
* [bottle](https://pypi.python.org/pypi/bottle/)
* [ldap3](https://pypi.python.org/pypi/ldap3) 2.x
* [waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/)

## Start the app

1. Copy `settings.ini.example` to `settings.ini` and edit it for your needs.
2. Copy the ca certificate to the filename provided via the `ca_cert` parameter in settings.ini.
3. \[optional\] Copy [wordlists](wordlists/README.md)) to the `wordlist` directory.
4. Build docker image:
    ```
   docker build -t ldap-passwd-ui .
   ```
5. Start the container
    ```
   docker run -it --rm -p "127.0.0.1:8080:8080"  --name ldap-passwd-ui ldap-passwd-ui
   ```
6. Access the app via webbrowser at http://127.0.0.1:8080

**Important:**
For use in production, you have to put the service behind a secure reverse proxy. An example for nginx can be found in
the [original docs](https://github.com/jirutka/ldap-passwd-webui#run-with-uwsgi-and-nginx)

## License

This project is licensed under [MIT License](http://opensource.org/licenses/MIT/). For the full text of the license, see
the [LICENSE](LICENSE) file.

## Screenshot

<p align="center"><img src="doc/screenshot.png" width="400"></p>



