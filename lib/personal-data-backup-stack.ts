import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sm from "aws-cdk-lib/aws-secretsmanager";

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
      handler: "lastfm.handler",
      timeout: Duration.minutes(5),
    });

    const backupSecret = sm.Secret.fromSecretAttributes(this, "BackupSecret", {
      secretCompleteArn: "arn:aws:secretsmanager:us-east-1:601028919375:secret:personal-backup-keys-uCEv0j",
    })
    backupSecret.grantRead(backupHandler);

    const backupBucket = new s3.Bucket(this, "BackupBucket");
    backupBucket.grantWrite(backupHandler);
  }
}
