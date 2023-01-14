import json
import boto3
import datetime
import csv
import os


# Environment Variables 

s3_bucket = os.environ["bucket_name"]


def get_free_size(cw_client, drive, stime, etime):


    response = cw_client.get_metric_statistics(
        Namespace='CWAgent-prom',
        MetricName='windows_logical_disk_free_bytes',
        Dimensions=[
            {
                'Name': 'volume',
                'Value': drive
            } 
        ],
        StartTime=stime,
        EndTime=etime,
        Period=60,
        Statistics=['Average'],
    )

    return response

def get_total_size(cw_client, drive, stime, etime):


    response = cw_client.get_metric_statistics(
        Namespace='CWAgent-prom',
        MetricName='windows_logical_disk_size_bytes',
        Dimensions=[
            {
                'Name': 'volume',
                'Value': drive
            } 
        ],
        StartTime=stime,
        EndTime=etime,
        Period=60,
        Statistics=['Average'],
    )

    return response




def lambda_handler(event, context):

    s3_client = boto3.client('s3')
    cw_client = boto3.client('cloudwatch')
    ec2_client = boto3.client('ec2')


    fields = ['InstanceName', 'InstanceId', 'Disk Name', 'Disk Total Size', 'Disk Initial Usage', 'Disk Final Usage']

    x = datetime.datetime.now()
    time=x.strftime("%d%m%Y%H%M%S")
    filename = "disk-utilization-" + time + ".csv"
    dest_file = "disk-utilization-" + time + ".csv"
        
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        
        
    ec2_response = ec2_client.describe_instances()
    inst_count = len(ec2_response['Reservations'])


    for i in range(inst_count):
        # try:
        instance_id = ec2_response['Reservations'][i]['Instances'][0]['InstanceId']
        
        ec2_details = ec2_response['Reservations'][i]['Instances'][0]['Tags']
        instance_name = next((item["Value"] for item in ec2_details if item["Key"] == "Name"), None)

        disk = cw_client.list_metrics(Namespace='CWAgent-prom',MetricName='windows_logical_disk_free_bytes')

        disk_count = len(disk['Metrics'])
        
        if disk_count == 0:
            print("Storage metrics not collected for server: " + instance_id)
        
        else:

            for j in range(disk_count):
                drive = disk['Metrics'][j]['Dimensions'][0]['Value']
                drive_name= drive + "Drive"


                disk_total_size = get_total_size(cw_client, drive, datetime.datetime(2023, 1, 14, 10, 30), datetime.datetime(2023, 1, 14, 10, 50))
                disk_total=str(int(disk_total_size['Datapoints'][0]['Average']/1024/1024/1024 +0.5)) + 'GB'

                disk_initial_usage = get_free_size(cw_client, drive, datetime.datetime(2023, 1, 14, 10, 30), datetime.datetime(2023, 1, 14, 10, 50))
                initial_usage_size=str(int(disk_initial_usage['Datapoints'][0]['Average']/1024/1024/1024 +0.5)) + "GB"

                disk_final_usage = get_free_size(cw_client, drive, datetime.datetime(2023, 1, 14, 10, 30), datetime.datetime(2023, 1, 14, 10, 50))
                final_usage_size=str(int(disk_final_usage['Datapoints'][0]['Average']/1024/1024/1024 +0.5)) + "GB"



                rows = [ [instance_name, instance_id, drive_name, disk_total, initial_usage_size, final_usage_size] ]
        
                with open(filename, 'a') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerows(rows)

    s3_client.upload_file(filename, s3_bucket, dest_file)


