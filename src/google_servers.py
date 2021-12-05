# reducing this to the two LB hostnames - however needs testing whether this uses round-robin
# or sticky sessions, in which case throttling become an issue again
GOOGLE_SERVERS = [
    'mt.google.com',
    "khm.google.com",
    "khms.google.com",
]
