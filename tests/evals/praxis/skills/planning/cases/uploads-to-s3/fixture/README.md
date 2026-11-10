# acme-docs

A document-sharing web app on three servers behind a load balancer. Deploys replace one
server at a time.

Uploads live in `/srv/uploads`, an NFS share from one storage box that all three servers
mount. There are about 2 TB in 9 million files, and users add about 20,000 files a day.
Download links look like `/uploads/<id>/<name>` and sit in years of emails and shared
documents.
