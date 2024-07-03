# Backlog-dl

Backlog shared file downloader.

## Installation

```
$ pip install git+https://github.com/lotusshinoaki/backlog-dl.git
```

## Set enviroments

```
$ export BACKLOG_API_KEY=<YOUR BACKLOG API KEY>
$ export BACKLOG_DOMAIN=<YOUR BACKLOG DOMAIN>

# Example
# export BACKLOG_API_KEY=c7cff5a86f873f714633781cd0ed59a3
# export BACKLOG_DOMAIN=47f54c72.backlog.jp
```

## List all shared files

```
$ backlog_dl list-shared-files <PROJECT_ID>
```

## Download all shared files

```
$ backlog_dl download-shared-files <PROJECT_ID>
```
