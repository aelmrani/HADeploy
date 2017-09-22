# maven_repositories

## Synopsis

Provide a list maven repositories to fetch artifact from

## Attributes

Each item of the list has the following attributes:

Name | req? | 	Description
--- | ---  | ---
name|yes|Local name of this repository. Will be used for reference in a [`file`](./files)  with `src: "mvn//<repoName>/..."`
url|yes|The URL of the Maven Repository to download from.
username|no|The username to authenticate as to the Maven Repository, in case of access control.
password|no|Associated password
timeout|no|Specifies a timeout in seconds for the connection attempt. Default: `10`
validate_certs|no|Boolean; In case of `src: https://...` Setting to false, will disable strict certificate checking, thus allowing self-signed certificate.<br>Default: `yes`

## Example

The traditionnal public maven repository:

```yaml
maven_repositories:
- name: maven2
  url: "http://repo1.maven.org/maven2/"
```

A local, private repository, requiring user authentication, and accessed using SSL, but with an invalid certificate:

```yaml
- name: nexus_snapshots
  url: https://nexus_server.local/nexus/content/repositories/snapshots/
  username: john
  password: aNicePassword
  validate_certs: no
```

As released artifact are under another URL, you may have to define another one for releases:

And here, we also adopt the good practice of encrypting the password.

```yaml

encrypted_vars:
  john_password: |
    $ANSIBLE_VAULT;1.1;AES256
    65626166653134326137613232323336373139393036383532333863623630363662303531306539
    6637306363343836376633353439656634613638643031660a636238323663353337313333663438
    30306234306463626338663637623563393735653237323833323064316561653237393538303762
    6363326232656461310a656631386135663764386565366566633537633665646562626236393462
    6231


- name: nexus_releases
  url: https://nexus_server.local/nexus/content/repositories/releases/
  username: john
  password: "{{john_password}}"
  validate_certs: no
```

Refer to [encrypted variables](../core/encrypted_vars) for more information.
