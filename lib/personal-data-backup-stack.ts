import { Stack, StackProps } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";

import { Construct } from 'constructs';

import { BackupLambda } from './lambda';
import { BackupRole } from './iam';

export class PersonalDataBackupStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, "BackupBucket");
    const role = new BackupRole(this, 'BackupRole', {
      bucket: bucket,
    });
    
    new BackupLambda(this, 'LastFMLambda', {
      handler: 'lastfm.handler',
      role: role.getRole(),

    });

    new BackupLambda(this, 'TogglLambda', {
      handler: 'toggl.handler',
      role: role.getRole(),
    });
  }
}
