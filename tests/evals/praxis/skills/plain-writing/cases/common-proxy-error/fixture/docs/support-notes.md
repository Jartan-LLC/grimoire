# Support notes

The failure most users report is `SSL: CERTIFICATE_VERIFY_FAILED` behind a company proxy. Setting
`REQUESTS_CA_BUNDLE` to the company CA file fixes it.
