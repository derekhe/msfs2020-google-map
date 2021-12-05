# reducing this to the two LB hostnames - however needs testing whether this uses round-robin
# or sticky sessions, in which case throttling become an issue again
GOOGLE_SERVERS = [
    'mt.google.com',
    "khm.google.com",
    "khms.google.com",
    "142.250.66.174",
    "172.217.24.46",
    "142.250.71.78",
]
