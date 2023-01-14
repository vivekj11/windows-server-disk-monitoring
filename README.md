# Project Highlight


To monitor EC2 windows virtual machine, specially the metrics which are not available by default such as disk utilization, memory utilization etc.

Once the metrics are available, generate a csv report for a particular day/ month and place them in an s3 bucket. 


# Tool Selection

There are various tools available to do that and aws itself provides aws cloudwatch agent to pull the metrics and ingest them in cloudwatch.

One specific requirement that the cloud watch does not fulfil is to get the disk utilization in GBs. I mean, it does give the disk utilization % but not the actual size of disk and the used size. 
Due to this limitation, I ahve used one more open source tool called windows_exporter.


Based on our requirement, we can choose any of them.

#  Hands-on 

I have dividied this lab in two catagories.

1. To monitor the disk utilization using aws cloudwatch agent and plot the default usage %. 

2. To monitor the disk utilziation and get the actual disk size and usage size. We are going to to get these details using windows_exporter. The windows_exporter share the metrics in TimeSeries format (prometheus format) which can be picked by cloudwatch agent or any other similar tool.


In both the cases, we create a lambda function that will execute this python script as and when we need.


</br>

# using cloudWatch agent and getting default metrics

A list of all default metrics provided by cloudwatch agent can be found [here](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-collected-by-CloudWatch-agent.html). 


Installing cloudwatch agent in windows server--

1. Login to the Windows server and put the below URL in browser to download the package.. 


        https://s3.amazonaws.com/amazoncloudwatch-agent/windows/amd64/latest/amazon-cloudwatch-agent.msi


2. Once downlaoded, install it either by doublecliking on it ir using CMD/Powershell in admin mode.

        msiexec /i amazon-cloudwatch-agent.msi


3. Now its time to generate the config file. By default, Agent keeps the script files and config files at "C:\Program Files\Amazon\AmazonCloudWatchAgent". 

    Go inside this folder and run below command from powershell to generate the config


        cd C:\Program Files\Amazon\AmazonCloudWatchAgent

        ./amazon-cloudwatch-agent-config-wizard.exe

    provide the response to all the points as per your requirement. Once done, you will see a new file in the folder as config.json



4. Finally, its time to run the agent using below command

        & "C:\Program Files\Amazon\AmazonCloudWatchAgent\amazon-cloudwatch-agent-ctl.ps1" -a fetch-config -m ec2 -s -c file:"C:\Program Files\Amazon\AmazonCloudWatchAgent\config.json"


5. you also need to provide aws credentials either using access key and secret access key or by attaching an IAM Role.

    I have used EC2 IAM role for this setup with CloudWatchFullAcess (we can reduce the permissions once the setup is completed.) 

6. Go to your CloudWatch dashbaord and you will be able to see some metrics in CWAgent namespace.


</br>

Now its time to create the lambda function to generate the report.


- The python code is available in lambda format. Make a zip file out of it and then run the terraform code to create the lambda function in aws cloud.

        zip get-disk-package.zip lambda_function.py
        terraform apply 

- I have used the bucket name as a variable that you can update in main.tf terraform file.

- I have used one IAM role for this lambda function that has default cloudwatch permissions and EC2, S3 permissions to describe the server and upload the file to s3 bucket.

TODO: Create the IAM role its permission as a part of terraform code itself. 


</br>


In case, you are not a fan of terraform, Just create a lambda function manually in AWS cloud and copy paste the entire code of lambda_function.py file. 
Also, make sure to update the s3 bucket name in the code and to provide the relevant permissions to the associated IAM role.  


</br>


# Using windows_exporter to get more metrics

Like explained before, cloudwatch agent provides limited metrics and perheps those are not sufficient as per your reuqirement. 

There are different tools available in the market that we can use to get more metrics. 

- I personally like this windows_exporter since it is based on proemtheus time series and these metrics can be integrated with prometheus in future. And also, this is backed by promethues community only. 


1. Download the windows_exporter package inside the EC2 windows server from the below link 

        https://github.com/prometheus-community/windows_exporter/releases/


2. Install it by double clinking on the package or run the below command for some fine tuning such as port number.

        cd C:\Users\Administrator\Downloads
        msiexec /i <path-to-msi-file> ENABLED_COLLECTORS=logical_disk LISTEN_PORT=5000


3. That's it, you will get the metrics at  "http://localhost:5000". If you run it with default configs, metrics will be available on port 9182. 


Now these metrics can be shared with prometheus and other destinations. For this lab, we are going to share the metrics with CloudWatch.

</br>

## sharing the metrics with cloudwatch


Now, Though cloudwatch agent also supports the prometheus metrics now but I did not find any helpful resource to make this work.

I choose an opensource package developed by CloudPoose. Here is the github [page](https://github.com/cloudposse/prometheus-to-cloudwatch) 

</br>

> *It is good idea to share only required metrics as sharing all metrics with cloudwatch can be costly in long run*

1. Download the package in your windows server from given page-

        https://github.com/cloudposse/prometheus-to-cloudwatch/releases/tag/0.14.0


2. Now run this tool from powershell using below command. I ahve specially choosen the disk metrics to share with cloudwatch.

        cd C:\Users\Administrator\Downloads

        ./prometheus-to-cloudwatch_windows_386.exe -cloudwatch_namespace=CWAgent-prom -cloudwatch_region=us-east-1 -prometheus_scrape_url=http://127.0.0.1:5000/metrics -include_metrics='windows_disk*'

3. In sometime, you should be able to see metrics in cloudwatch.


</br>

Now its time to create the lambda function to generate the report.


- The python code is available in lambda format. Make a zip file out of it and then run the terraform code to create the lambda function in aws cloud.

        zip get-disk-package.zip lambda_function.py
        terraform apply 

- I have used the bucket name as a variable that you can update in main.tf terraform file.

- I have used one IAM role for this lambda function that has default cloudwatch permissions and EC2, S3 permissions to describe the server and upload the file to s3 bucket.

TODO: Create the IAM role its permission as a part of terraform code itself. 

