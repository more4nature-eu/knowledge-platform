
import hashlib
import requests

from django.conf import settings

def subscribe_to_mailchimp(data, api_key, audience_id):
    email = data.get('email', None)
    name = data.get('name', None)
    organization = data.get('organization', None)

    member_hash = hashlib.md5(
        email.lower().encode()
    ).hexdigest()

    fname, *lname = name.split(' ')

    merge_fields = {"FNAME": fname}

    if lname:
        merge_fields["LNAME"] = lname[0]

    if organization:
        merge_fields["ORG_TYPE"] = organization
        merge_fields["ORG_TYPE_O"] = organization

    url = (
        f"https://{api_key.split("-")[-1]}.api.mailchimp.com/3.0"
        f"/lists/{audience_id}/members/{member_hash}"
    )

    headers = {'Content-Type': 'application/json'}

    response = requests.put(
        url,
        auth=("anystring", api_key),
        headers=headers,
        json={
            "email_address": email,
            "merge_fields": merge_fields,
            "status_if_new": "subscribed",
        },
        timeout=10,
    )

    response.raise_for_status()