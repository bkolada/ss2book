# ss2book

# install

## Kali GNU/Linux 2.0 // Debian 8 Jessie

```
# libs for scrapy
# apt-get install python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
$cd ss2book
$ virtualenv env
$ source env/bin/activate
$ pip install -U setuptools
$ pip install -U pip
$ pip install -r requirements
```

# run

## run fuse exporter
```
$ source env/bin/activate
$ source env_vars
$ scrapy crawl skillport -a book_id=12345 --set FEED_URI=tmp/all.html --set FEED_FORMAT=fuse
```
