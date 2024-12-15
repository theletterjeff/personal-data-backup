import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";

import { Construct } from 'constructs';

interface IamProps {
  bucket: s3.Bucket,
}

export class BackupRole extends Construct {
  public readonly role: iam.Role;

  constructor(scope: Construct, id: string, props: IamProps) {
    super(scope, id);

    this.role = new iam.Role(this, "BackupLambdaRole", {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    const putObjectPolicy = new iam.PolicyStatement({
      actions: ["s3:PutObject"],
      resources: [props.bucket.bucketArn + "/*"],
    });
    this.role.addToPolicy(putObjectPolicy);
  }

  public getRole(): iam.Role {
    return this.role;
  }
}
