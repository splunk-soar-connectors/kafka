[comment]: # " File: README.md"
[comment]: # "  Copyright (c) 2017-2022 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
## Kerberos Authentication

If you wish to authenticate with the Kafka instance using Kerberos, the following items are needed:

-   A Kerberos Principal will be needed for " **phantom** "
-   Normal Kerberos requirements (KDC, Keytabs, Principals, etc) still apply
-   **kinit** must be run for the **phantom** principal, for the **phantom-worker** user
-   It should be noted that Kerberos tickets will expire, so it is recommended to use a script to
    run **kinit** periodically to refresh the ticket for **phantom-worker**

## SSL Authentication

To authenticate with the Kafka instance using SSL, the following configuration parameters may be
required. They are to be pointed to the location of certain files:

-   **cert_file** - A signed certificate file that is trusted by the Kafka instance
-   **key_file** - The key used to generate **cert_file**
-   **ca_cert** - The certificate of the certificate authority that signed **cert_file**

It is recommended that these files be placed under the **\<PHANTOM_HOME>/etc/ssl/** directory. These
files must be readable by the **phantom-worker** user.  
  
Note that not all of these files will be necessary for all setups. More than likely, **cert_file**
will be required. However, the other parameters will be needed in certain cases. For example,
**ca_cert** will be needed if you set up your own certificate authority.

## GSSAPI

The Kerberos authentication for this app uses the python-gssapi module, which is licensed under the
ISC License, Copyright (c) 2014, The Python GSSAPI Team.
