import { Duration } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as sm from "aws-cdk-lib/aws-secretsmanager";
import * as scheduler from "@aws-cdk/aws-scheduler-alpha";
import * as targets from "@aws-cdk/aws-scheduler-targets-alpha";

import { Construct } from 'constructs';

interface LambdaProps {
  handler: string,
  role: iam.Role,
}

export class BackupLambda extends Construct {
  constructor(scope: Construct, id: string, props: LambdaProps) {
    super(scope, id);

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
      handler: props.handler,
      timeout: Duration.minutes(10),
      role: props.role,
    });

    // for API keys
    const backupSecret = sm.Secret.fromSecretAttributes(this, "BackupSecret", {
      secretCompleteArn: "arn:aws:secretsmanager:us-east-1:601028919375:secret:personal-backup-keys-uCEv0j",
    })
    backupSecret.grantRead(backupHandler);

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
  const startOfCurrentMonth = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      1,
      0, 0, 0, 0,
    ),
  );
  const endOfLastMonth = new Date(startOfCurrentMonth.getTime() - 1000);
  const startOfLastMonth = new Date(
    Date.UTC(
      endOfLastMonth.getUTCFullYear(),
      endOfLastMonth.getUTCMonth(),
      1,
      0, 0, 0, 0,
    ),
  );
  return {
    start: Math.floor(startOfLastMonth.getTime() / 1000),
    end: Math.floor(endOfLastMonth.getTime() / 1000)
  };
}
