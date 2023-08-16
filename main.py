import boto3


def create_alarm(cloudwatch_client, instance_id, metric_name, threshold, comparison_operator):
    alarm_name = f"{metric_name}-Alarm-{instance_id}"

    response = cloudwatch_client.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription=f"Alarm for {metric_name} {comparison_operator} {threshold}%",
        ActionsEnabled=False,  # Change to True if you want actions enabled
        MetricName=metric_name,
        Namespace="AWS/EC2",
        Statistic="Average",  # Or "Maximum" based on your requirement
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            },
        ],
        Period=300,  # 5 minutes
        EvaluationPeriods=1,
        Threshold=threshold,
        ComparisonOperator=comparison_operator,
        AlarmActions=[],  # Add SNS topic ARNs or other actions if desired
    )

    print(f"Alarm created for {instance_id}: {alarm_name}")


def get_instances_with_no_alarms(ec2_client, cloudwatch_client):
    instances_with_no_alarms = []

    # Get all EC2 instances
    instances = ec2_client.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']

            # Get all CloudWatch alarms
            alarms = cloudwatch_client.describe_alarms()

            # Check if any alarms are associated with the instance
            alarms_for_instance = [
                alarm for alarm in alarms['MetricAlarms']
                if any(dimension['Name'] == 'InstanceId' and dimension['Value'] == instance_id
                       for dimension in alarm['Dimensions'])
            ]

            if not alarms_for_instance:
                instances_with_no_alarms.append(instance_id)
                create_alarm(cloudwatch_client, instance_id, "CPUUtilization", 90, "GreaterThanOrEqualToThreshold")
                create_alarm(cloudwatch_client, instance_id, "StatusCheckFailed", 1, "GreaterThanOrEqualToThreshold")

    return instances_with_no_alarms


def main():
    # Set up Boto3 clients
    ec2_client = boto3.client('ec2')
    cloudwatch_client = boto3.client('cloudwatch')

    instances_with_no_alarms = get_instances_with_no_alarms(ec2_client, cloudwatch_client)

    print("Instances with no CloudWatch alarms:")
    for instance_id in instances_with_no_alarms:
        print(instance_id)


if __name__ == "__main__":
    main()
