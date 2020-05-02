import authorization
import base64
import email
from apiclient import errors

service_gmail, service_drive, service_sheets = authorization.main()

def get_messages(service, user_id):
    try:
        return service.users().messages().list(userId=user_id).execute()
    except Exception as error:
        print('An error occurred: %s' % error)


def get_message(service, user_id, msg_id):
    try:
        return service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute()
    except Exception as error:
        print('An error occurred: %s' % error)


def get_mime_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='raw').execute()
        print('Message snippet: %s' % message['snippet'])
        msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8")).decode("utf-8")
        mime_msg = email.message_from_string(msg_str)

        return mime_msg
    except Exception as error:
        print('An error occurred: %s' % error)


def get_attachments(service, user_id, msg_id, store_dir):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        for part in message['payload']['parts']:
            if (part['filename'] and part['body'] and part['body']['attachmentId']):
                attachment = service.users().messages().attachments().get(id=part['body']['attachmentId'],
                                                                          userId=user_id, messageId=msg_id).execute()

                file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))
                path = ''.join([store_dir, part['filename']])

                f = open(path, 'wb')
                f.write(file_data)
                f.close()
    except Exception as error:
        print('An error occurred: %s' % error)


filter_one = {
    'id': 'attachmentFilter',
    'criteria': {
        'hasAttachment': True
    }
    'action': {
        'addLabelIds': ['hasAttachment']
    }
}

def getMatchingThreads(service,userId,labelIds,query):
    """Get all threads from gmail that match the query"""

    response = service.users().threads().list(userId=userId,labelIds=labelIds,
        q=query).execute()
    threads = []
    if 'threads' in response:
        threads.extend(response['threads'])

    # Do the response while there is a next page to receive.
    while 'nextPageToken' in response:
        pageToken = response['nextPageToken']
        response = service.users().threads().list(
            userId=userId,
            labelIds=labelIds,
            q=query,
            pageToken=pageToken).execute()
        threads.extend(response['threads'])

    return threads

def buildSearchQuery(criteria):
    """Input is the criteria in a filter object. Iterate over it and return a
    gmail query string that can be used for thread search"""

    queryList = []
    positiveStringKeys = ["from","to","subject"]
    for k in positiveStringKeys:
        v = criteria.get(k)
        if v is not None:
            queryList.append("("+k+":"+v+")")

    v = criteria.get("query")
    if v is not None:
        queryList.append("("+v+")")

    # TODO: This can be extended to include other queries. Negated queries,
    # non-string queries

    return " AND ".join(queryList)

def applyFilterToMatchingThreads(service,userId,filterObject):
    """After creating the filter we want to apply it to all matching threads
    This function searches all threads with the criteria and appends the same
    label of the filter"""

    query = buildSearchQuery(filterObject["criteria"])
    threads = getMatchingThreads(service,userId,[],query)

    addLabels = filterObject["action"]["addLabelIds"]
    print("Adding labels {} to {} threads".format(addLabels,len(threads)))

    for t in threads:
        body = {
            "addLabelIds": addLabels,
            "removeLabelIds": []
        }
        service.users().threads().modify(userId=userId,id=t["id"],
            body=body).execute()


def create_filter(service, userId, filterObject):
    try:
        filter = service.users().settings().filters().create(userId=userId, body=filterObject).execute()
        print("Created filter {}".format(filter.get('id')))
        return filter
    except Exception as error:
        print('An error occurred: %s' % error)






def CreateLabel(service, user_id, label_object):
  try:
    label = service.users().labels().create(userId=user_id,
                                            body=label_object).execute()
    print(label['id'])
    return label
  except errors.HttpError as error:
    print('An error occurred: %s' % error)


def MakeLabel(label_name, mlv='show', llv='labelShow'):
  label = {'messageListVisibility': mlv,
           'name': label_name,
           'labelListVisibility': llv}
  return label