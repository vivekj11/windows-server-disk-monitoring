import json
import boto3
import datetime
import csv
import os


# Environment Variables 

s3_bucket = os.environ["bucket_name"]


def get_stats(cw_client, InstanceId, drive, ImageId, InstanceType, stime, etime):
    
    response = cw_client.get_metric_statistics(
        Namespace='CWAgent',
        MetricName='LogicalDisk % Free Space',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': InstanceId
            },
             {
                'Name': 'instance',
                'Value': drive
            },
            {
                'Name': 'objectname',
                'Value': 'LogicalDisk'
            },
                         {
                'Name': 'ImageId',
                'Value': ImageId
            },
                         {
                'Name': 'InstanceType',
                'Value': InstanceType
            }
        ],
        StartTime=stime,
        EndTime=etime,
        Period=86400,
        Statistics=['Average'],
    )
    return response


def lambda_handler(event, context):

    s3_client = boto3.client('s3')
    cw_client = boto3.client('cloudwatch')
    ec2_client = boto3.client('ec2')


    fields = ['InstanceId', 'Drive', 'initial_value', 'final_value']

    x = datetime.datetime.now()
    time=x.strftime("%d%m%Y%H%M%S")
    filename = "/tmp/disk-utilization-" + time + ".csv"
    dest_file = "disk-utilization-" + time + ".csv"
    
    with open(filename, 'w') as csvfile:
       csvwriter = csv.writer(csvfile)
       csvwriter.writerow(fields)
    
    
    ec2_response = ec2_client.describe_instances()
    inst_count = len(ec2_response['Reservations'])

    for i in range(inst_count):
        # try:
        instance_id = ec2_response['Reservations'][i]['Instances'][0]['InstanceId']
        image_id = ec2_response['Reservations'][i]['Instances'][0]['ImageId']
        instance_type = ec2_response['Reservations'][i]['Instances'][0]['InstanceType']
        # instance_name = ec2_response['Reservations'][i]['Instances'][0]['Tags'][0]['Value']
        # TODO: Provide a name of Instance, but this field will not work if there is any other tag before Name tag


        print(instance_id)
 
        disk = cw_client.list_metrics(Namespace='CWAgent',MetricName='LogicalDisk % Free Space',Dimensions=[{'Name': 'InstanceId','Value': instance_id},{'Name': 'objectname','Value': 'LogicalDisk'}])
    
        disk_count = len(disk['Metrics'])
        
        if disk_count == 0:
            print("Storage metrics not collected for server: " + instance_id)
        
        else:

            for j in range(disk_count):
                drive = disk['Metrics'][j]['Dimensions'][0]['Value']

                initial_value = get_stats(cw_client, instance_id, drive, image_id, instance_type, datetime.datetime(2023, 1, 11, 0, 5), datetime.datetime(2023, 1, 11, 23, 45))
                initial_usage=str(round(initial_value['Datapoints'][0]['Average'], 2)) + "%"
    
                final_value = get_stats(cw_client, instance_id, drive, image_id, instance_type, datetime.datetime(2023, 1, 11, 0, 5), datetime.datetime(2023, 1, 11, 23, 45))
                final_usage=str(round(final_value['Datapoints'][0]['Average'], 2)) + "%"

    
                rows = [ [instance_id, drive, initial_usage, final_usage] ]
        
                with open(filename, 'a') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerows(rows)

    s3_client.upload_file(filename, s3_bucket, dest_file)


