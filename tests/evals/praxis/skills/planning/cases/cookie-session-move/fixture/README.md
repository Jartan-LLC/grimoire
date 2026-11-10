# acme pay

The web app is served from <https://app.acme.com> and calls the API at <https://api.acme.com>
(`server/`, Flask). A login creates a session that lasts 30 days; at any time about 8,000
users have one. The web app and the API deploy separately, each on merge to main.
