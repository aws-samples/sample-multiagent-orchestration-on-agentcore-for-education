#!/usr/bin/env python3
"""
Deploy Cognito User Pool for Octank Educational Multi-Agent System

This script creates a Cognito User Pool identical to us-east-1_sUJtYFJc1
with all the necessary configuration for the educational system.
"""

import boto3
import json
import os
import sys
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_phone_number(phone_number):
    """
    Validate phone number format
    """
    import re
    # Basic validation for international phone numbers
    pattern = r'^\+[1-9]\d{1,14}$'
    return re.match(pattern, phone_number) is not None

def create_cognito_user_pool():
    """
    Create Cognito User Pool with the same configuration as us-east-1_sUJtYFJc1
    """
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp')
    
    # Get AWS account and region info
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    region = boto3.Session().region_name
    
    print(f"🚀 Creating Cognito User Pool in {region} (Account: {account_id})")
    
    try:
        # Create User Pool with identical configuration
        user_pool_response = cognito_client.create_user_pool(
            PoolName='OctankEduMultiAgentPool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': True,
                    'TemporaryPasswordValidityDays': 7
                }
            },
            DeletionProtection='INACTIVE',
            Schema=[
                # Standard attributes
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True,
                    'StringAttributeConstraints': {
                        'MinLength': '0',
                        'MaxLength': '2048'
                    }
                },
                {
                    'Name': 'phone_number',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'StringAttributeConstraints': {
                        'MinLength': '0',
                        'MaxLength': '2048'
                    }
                },
                {
                    'Name': 'given_name',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'StringAttributeConstraints': {
                        'MinLength': '0',
                        'MaxLength': '2048'
                    }
                },
                {
                    'Name': 'family_name',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'StringAttributeConstraints': {
                        'MinLength': '0',
                        'MaxLength': '2048'
                    }
                },
                {
                    'Name': 'name',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'StringAttributeConstraints': {
                        'MinLength': '0',
                        'MaxLength': '2048'
                    }
                },
                # Custom attribute for persona (CRITICAL for the system)
                {
                    'Name': 'persona',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True,
                    'StringAttributeConstraints': {}
                }
            ],
            VerificationMessageTemplate={
                'DefaultEmailOption': 'CONFIRM_WITH_CODE'
            },
            MfaConfiguration='OFF',
            EmailConfiguration={
                'EmailSendingAccount': 'COGNITO_DEFAULT'
            },
            AdminCreateUserConfig={
                'AllowAdminCreateUserOnly': False
            },
            AccountRecoverySetting={
                'RecoveryMechanisms': [
                    {
                        'Priority': 1,
                        'Name': 'verified_email'
                    },
                    {
                        'Priority': 2,
                        'Name': 'verified_phone_number'
                    }
                ]
            },
            UserAttributeUpdateSettings={
                'AttributesRequireVerificationBeforeUpdate': []
            }
        )
        
        user_pool_id = user_pool_response['UserPool']['Id']
        print(f"✅ User Pool created successfully: {user_pool_id}")
        
        # Create domain for the user pool
        domain_name = user_pool_id.replace('_', '').lower()
        try:
            cognito_client.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=user_pool_id
            )
            print(f"✅ Domain created: {domain_name}")
        except ClientError as e:
            if 'InvalidParameterException' in str(e):
                print(f"⚠️ Domain already exists or invalid: {domain_name}")
            else:
                print(f"❌ Error creating domain: {e}")
        
        # Create groups
        groups = [
            {
                'GroupName': 'administrator',
                'Description': 'Grupo de administradores do sistema educacional Octank',
                'Precedence': 1
            },
            {
                'GroupName': 'professor',
                'Description': 'Grupo de professores e educadores do sistema Octank',
                'Precedence': 2
            },
            {
                'GroupName': 'student',
                'Description': 'Grupo de estudantes do sistema educacional Octank',
                'Precedence': 3
            }
        ]
        
        for group in groups:
            try:
                cognito_client.create_group(
                    GroupName=group['GroupName'],
                    UserPoolId=user_pool_id,
                    Description=group['Description'],
                    Precedence=group['Precedence']
                )
                print(f"✅ Group created: {group['GroupName']}")
            except ClientError as e:
                print(f"❌ Error creating group {group['GroupName']}: {e}")
        
        # Get demo user phone numbers from environment variables
        demo_admin_phone = os.getenv('DEMO_ADMIN_PHONE')
        demo_professor_phone = os.getenv('DEMO_PROFESSOR_PHONE')
        demo_student_phone = os.getenv('DEMO_STUDENT_PHONE')
        
        # Validate phone numbers
        if not all([demo_admin_phone, demo_professor_phone, demo_student_phone]):
            print("⚠️ Warning: Demo phone numbers not found in environment variables.")
            print("   Please set DEMO_ADMIN_PHONE, DEMO_PROFESSOR_PHONE, and DEMO_STUDENT_PHONE in .env file")
            print("   Using default phone numbers for demo...")
            demo_admin_phone = '+5511987654321'
            demo_professor_phone = '+551146731805'
            demo_student_phone = '+5511123456789'
        else:
            # Validate phone number formats
            phone_numbers = [
                ('DEMO_ADMIN_PHONE', demo_admin_phone),
                ('DEMO_PROFESSOR_PHONE', demo_professor_phone),
                ('DEMO_STUDENT_PHONE', demo_student_phone)
            ]
            
            for var_name, phone in phone_numbers:
                if not validate_phone_number(phone):
                    print(f"❌ Invalid phone number format for {var_name}: {phone}")
                    print("   Phone numbers must be in international format: +[country_code][area_code][number]")
                    print("   Example: +5511987654321")
                    return None
        
        # Create demo users
        demo_users = [
            {
                'username': 'admin_demo',
                'email': 'admin@octank.edu',
                'phone': demo_admin_phone,
                'given_name': 'Admin',
                'family_name': 'Demo',
                'persona': 'administrator',
                'group': 'administrator'
            },
            {
                'username': 'professor_demo',
                'email': 'professor@octank.edu',
                'phone': demo_professor_phone,
                'given_name': 'Professor',
                'family_name': 'Demo',
                'persona': 'professor',
                'group': 'professor'
            },
            {
                'username': 'student_demo',
                'email': 'student@octank.edu',
                'phone': demo_student_phone,
                'given_name': 'Student',
                'family_name': 'Demo',
                'persona': 'student',
                'group': 'student'
            }
        ]
        
        for user in demo_users:
            try:
                # Create user
                cognito_client.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=user['username'],
                    UserAttributes=[
                        {'Name': 'email', 'Value': user['email']},
                        {'Name': 'phone_number', 'Value': user['phone']},
                        {'Name': 'given_name', 'Value': user['given_name']},
                        {'Name': 'family_name', 'Value': user['family_name']},
                        {'Name': 'custom:persona', 'Value': user['persona']},
                        {'Name': 'email_verified', 'Value': 'true'},
                        {'Name': 'phone_number_verified', 'Value': 'true'}
                    ],
                    TemporaryPassword='TempPass123!',
                    MessageAction='SUPPRESS'
                )
                
                # Set permanent password
                cognito_client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=user['username'],
                    Password='OctankDemo123!',
                    Permanent=True
                )
                
                # Add user to group
                cognito_client.admin_add_user_to_group(
                    UserPoolId=user_pool_id,
                    Username=user['username'],
                    GroupName=user['group']
                )
                
                print(f"✅ Demo user created: {user['username']} ({user['persona']})")
                
            except ClientError as e:
                print(f"❌ Error creating user {user['username']}: {e}")
        
        # Update .env file with new User Pool ID
        update_env_file(user_pool_id)
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 COGNITO USER POOL DEPLOYMENT COMPLETE!")
        print("="*60)
        print(f"User Pool ID: {user_pool_id}")
        print(f"Domain: {domain_name}")
        print(f"Region: {region}")
        print("\n📋 Demo Users Created:")
        for user in demo_users:
            print(f"  • {user['username']} ({user['persona']}) - Password: OctankDemo123!")
        print("\n📱 Phone Numbers for WhatsApp Testing:")
        for user in demo_users:
            print(f"  • {user['persona']}: {user['phone']}")
        print("\n🔧 Environment Variables Used:")
        print(f"  • DEMO_ADMIN_PHONE: {demo_admin_phone}")
        print(f"  • DEMO_PROFESSOR_PHONE: {demo_professor_phone}")
        print(f"  • DEMO_STUDENT_PHONE: {demo_student_phone}")
        print("\n⚠️ IMPORTANT:")
        print("  • .env file updated with new USER_POOL_ID")
        print("  • Demo passwords: OctankDemo123!")
        print("  • Users are in their respective groups")
        print("  • Custom persona attribute configured")
        
        return user_pool_id
        
    except ClientError as e:
        print(f"❌ Error creating User Pool: {e}")
        return None

def update_env_file(user_pool_id):
    """
    Update .env file with new User Pool ID
    """
    try:
        # Read current .env file
        env_file_path = '.env'
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                lines = f.readlines()
            
            # Update USER_POOL_ID line
            updated_lines = []
            user_pool_updated = False
            
            for line in lines:
                if line.startswith('USER_POOL_ID'):
                    updated_lines.append(f'USER_POOL_ID={user_pool_id}\n')
                    user_pool_updated = True
                else:
                    updated_lines.append(line)
            
            # Add USER_POOL_ID if not found
            if not user_pool_updated:
                updated_lines.append(f'USER_POOL_ID={user_pool_id}\n')
            
            # Write back to .env file
            with open(env_file_path, 'w') as f:
                f.writelines(updated_lines)
            
            print(f"✅ .env file updated with USER_POOL_ID: {user_pool_id}")
        else:
            print("⚠️ .env file not found, please add USER_POOL_ID manually")
            
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")

def check_environment_variables():
    """
    Check if required environment variables are set
    """
    required_vars = ['DEMO_ADMIN_PHONE', 'DEMO_PROFESSOR_PHONE', 'DEMO_STUDENT_PHONE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Missing environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n📝 Please add these variables to your .env file:")
        print("   DEMO_ADMIN_PHONE=+5511987654321")
        print("   DEMO_PROFESSOR_PHONE=+551146731805")
        print("   DEMO_STUDENT_PHONE=+5511123456789")
        print("\n💡 Phone numbers must be in international format: +[country][area][number]")
        return False
    
    return True

def main():
    """
    Main function
    """
    print("🚀 Octank Educational Multi-Agent System")
    print("📋 Cognito User Pool Deployment Script")
    print("-" * 50)
    
    # Check AWS credentials
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        sys.exit(1)
    
    # Check environment variables
    if not check_environment_variables():
        print("\n❌ Please configure the required environment variables before continuing.")
        sys.exit(1)
    
    # Create User Pool
    user_pool_id = create_cognito_user_pool()
    
    if user_pool_id:
        print(f"\n🎯 Next steps:")
        print(f"  1. Update your Lambda function with USER_POOL_ID: {user_pool_id}")
        print(f"  2. Test WhatsApp integration with demo phone numbers")
        print(f"  3. Deploy AgentCore Runtime with updated configuration")
    else:
        print("❌ Failed to create User Pool")
        sys.exit(1)

if __name__ == "__main__":
    main()