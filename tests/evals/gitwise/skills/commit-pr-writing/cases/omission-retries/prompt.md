`fetch_rates` should time out after 5 seconds instead of hanging forever. Add the timeout (the tests use
a fake opener, so no network), with a test, and commit. Don't add retries: the rates service bans
clients that retry, and the team still has to agree a policy with them.
