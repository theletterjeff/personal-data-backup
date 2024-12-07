import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sm from "aws-cdk-lib/aws-secretsmanager";
import * as scheduler from "@aws-cdk/aws-scheduler-alpha";
import * as targets from "@aws-cdk/aws-scheduler-targets-alpha";

import { Construct } from 'constructs';

export class PersonalDataBackupStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    
    const backupHandler = new lambda.Function(this, "BackupHandler", {
      runtime: lambda. Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset("lambda", {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
          ],
        },
      }),
      handler: "handler.handler",
      timeout: Duration.minutes(10),
    });

    // for API keys
    const backupSecret = sm.Secret.fromSecretAttributes(this, "BackupSecret", {
      secretCompleteArn: "arn:aws:secretsmanager:us-east-1:601028919375:secret:personal-backup-keys-uCEv0j",
    })
    backupSecret.grantRead(backupHandler);

    const backupBucket = new s3.Bucket(this, "BackupBucket");
    backupBucket.grantWrite(backupHandler);

    const target = new targets.LambdaInvoke(backupHandler, {
      retryAttempts: 3,
      input: scheduler.ScheduleTargetInput.fromObject(getLastMonthTimestamps()),
    });

    const schedule = new scheduler.Schedule(this, "BackupSchedule", {
      schedule: scheduler.ScheduleExpression.cron({
        minute: "0",
        hour: "0",
        day: "5",
      }),
      target,
    });
  }
}

function getLastMonthTimestamps(): { start: number; end: number } {
  const now = new Date();
  const startOfCurrentMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1, 0, 0, 0, 0));
  const endOfLastMonth = new Date(startOfCurrentMonth.getTime() - 1000); // Subtract 1 second to get to the last month in UTC
  const startOfLastMonth = new Date(Date.UTC(endOfLastMonth.getUTCFullYear(), endOfLastMonth.getUTCMonth(), 1, 0, 0, 0, 0));

  return {
    start: Math.floor(startOfLastMonth.getTime() / 1000),
    end: Math.floor(endOfLastMonth.getTime() / 1000)
  };
}
