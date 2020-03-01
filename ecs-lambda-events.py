#!/usr/bin/env python3
import json
from urllib import request

# read in sample event
with open('ecs-event.json') as file:
    data = json.load(file)

def lambda_handler(event):
    '''
    Parse AWS Event sent to a AWS Lambda Function in json format
    and send a message to slack is there is an ECS state change
    '''

    if event["source"] != "aws.ecs":
        raise ValueError("Function only supports input from events with "
                         "a source type of: aws.ecs")

    if event["detail-type"] == "ECS Task State Change":
        cluster_arn = event["detail"]["clusterArn"]
        cluster_name = parse_arn(cluster_arn)["resource"]
        container = event["detail"]["containers"][0]
        task_name = container["name"]
        task_last_status = container["lastStatus"]
        task_desired_status = event["detail"]["desiredStatus"]
        task_stop_reason = event["detail"]["stoppedReason"]
        msg = "Task {0} in cluster {1} changed from {2} to {3}" \
              "for reason {4}".format(task_name, cluster_name,
                                    task_last_status,
                                    task_desired_status, task_stop_reason)

        print(msg)
        send_slack(msg)

def parse_arn(arn):
    '''
    Convert AWS ARN into json
    '''
    # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    elements = arn.split(':', 5)
    res = {
        'arn': elements[0],
        'partition': elements[1],
        'service': elements[2],
        'region': elements[3],
        'account': elements[4],
        'resource': elements[5],
        'resource_type': None
    }
    if '/' in res['resource']:
        res['resource_type'], res['resource'] = res['resource'].split('/', 1)
    elif ':' in res['resource']:
        res['resource_type'], res['resource'] = res['resource'].split(':', 1)
    return res


def send_slack(text):
    '''
    send a message to channel
    '''
    
    base_url = "https://hooks.slack.com/services"
    acct_url_info = "API_INFO"
    webhook_url = "{0}/{1}".format(base_url, acct_url_info)
    slack_data = {"text": "{0}".format(text)}
    json_data = json.dumps(slack_data)

    req = request.Request(webhook_url, data=json_data.encode('ascii'),
                          headers={'Content-Type': 'application/json'})

    resp = request.urlopen(req)

    if resp.status != 200:
        raise ValueError("Request to slack failed code {}, the response is:\n " \
                         "{}".format(resp.status, resp.msg))


lambda_handler(data)
