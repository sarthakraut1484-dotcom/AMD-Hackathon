"""
Dataset Preparation Script for PRISM
Downloads and preprocesses scam/phishing datasets
"""

import os
import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split


def prepare_datasets():
    """
    Download and prepare training datasets
    Creates merged dataset with binary labels (0=Safe, 1=Scam)
    """
    print("🔄 Preparing datasets for PRISM...")
    
    # Create directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Load SMS Spam Collection Dataset
    print("\n📥 Loading SMS Spam Dataset...")
    try:
        sms_dataset = load_dataset('sms_spam', split='train')
        sms_df = pd.DataFrame(sms_dataset)
        sms_df['label'] = sms_df['label'].map({0: 0, 1: 1})  # 0=ham, 1=spam
        sms_df = sms_df.rename(columns={'sms': 'text'})
        print(f"   ✅ Loaded {len(sms_df)} SMS messages")
    except Exception as e:
        print(f"   ⚠️  Could not load sms_spam dataset: {e}")
        sms_df = pd.DataFrame()
    
    # Load Phishing Email Dataset
    print("\n📥 Loading Phishing Email Dataset...")
    try:
        # Using a public phishing dataset
        email_dataset = load_dataset('HeshamHaroon/phishing-legitimate-emails', split='train')
        email_df = pd.DataFrame(email_dataset)
        
        # Rename columns to match format
        if 'text' in email_df.columns and 'label' in email_df.columns:
            email_df = email_df[['text', 'label']]
        elif 'email' in email_df.columns:
            email_df = email_df.rename(columns={'email': 'text'})
            # Convert label if needed
            if 'label' in email_df.columns:
                email_df['label'] = email_df['label'].astype(int)
        
        print(f"   ✅ Loaded {len(email_df)} email messages")
    except Exception as e:
        print(f"   ⚠️  Could not load email dataset: {e}")
        email_df = pd.DataFrame()
    
    # Merge datasets
    print("\n🔗 Merging datasets...")
    if not sms_df.empty and not email_df.empty:
        merged_df = pd.concat([sms_df, email_df], ignore_index=True)
    elif not sms_df.empty:
        merged_df = sms_df
    elif not email_df.empty:
        merged_df = email_df
    else:
        print("❌ No datasets could be loaded. Creating sample dataset...")
        merged_df = create_sample_dataset()
    
    # Clean and preprocess
    print("\n🧹 Cleaning data...")
    merged_df = merged_df.dropna(subset=['text', 'label'])
    merged_df = merged_df.drop_duplicates(subset=['text'])
    merged_df['text'] = merged_df['text'].str.strip()
    merged_df = merged_df[merged_df['text'].str.len() > 10]  # Remove very short messages
    
    # Ensure binary labels
    merged_df['label'] = merged_df['label'].astype(int)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total messages: {len(merged_df)}")
    print(f"   Safe messages: {len(merged_df[merged_df['label'] == 0])}")
    print(f"   Scam messages: {len(merged_df[merged_df['label'] == 1])}")
    
    # Split train/test (80/20)
    print("\n✂️  Splitting train/test (80/20)...")
    train_df, test_df = train_test_split(
        merged_df,
        test_size=0.2,
        random_state=42,
        stratify=merged_df['label']
    )
    
    # Save processed datasets
    print("\n💾 Saving processed datasets...")
    train_df.to_csv('data/processed/train.csv', index=False)
    test_df.to_csv('data/processed/test.csv', index=False)
    
    print(f"   ✅ Train set: {len(train_df)} samples")
    print(f"   ✅ Test set: {len(test_df)} samples")
    
    print("\n✨ Dataset preparation complete!")
    print(f"   📁 Train: data/processed/train.csv")
    print(f"   📁 Test: data/processed/test.csv")


def create_sample_dataset():
    """
    Create a sample dataset if real datasets cannot be loaded
    """
    print("   Creating sample dataset for demonstration...")
    
    # Sample scam messages
    scam_messages = [
        "URGENT! Your bank account will be suspended. Click here immediately to verify: http://fake-bank.com",
        "Congratulations! You won $10,000 lottery. Send your credit card details to claim prize.",
        "Your order #12345 has failed. Update payment details now or account will be locked.",
        "FINAL NOTICE: Legal action will be taken. Pay fine immediately to avoid arrest.",
        "आपका बैंक खाता ब्लॉक हो जाएगा। तुरंत इस लिंक पर क्लिक करें।",
        "You have won a prize of Rs 50,000. Share your bank details and OTP to claim.",
        "Security alert! Someone logged into your account. Verify your password now.",
        "Limited time offer! Get instant loan approval. Call now: 98765-43210",
        "Your ATM card is blocked. Update KYC details immediately or face legal action.",
        "CONGRATULATIONS! You are selected for lottery prize. Send 500 rupees processing fee."
    ] * 50  # Repeat to get more samples
    
    # Sample safe messages
    safe_messages = [
        "Hey, are you free for coffee tomorrow?",
        "Meeting scheduled for 3 PM in conference room.",
        "Your Amazon order has been delivered successfully.",
        "Happy birthday! Wishing you a wonderful day ahead.",
        "कल शाम को मिलते हैं। धन्यवाद।",
        "The project deadline has been extended to Friday.",
        "Reminder: Doctor appointment at 5 PM today.",
        "Your OTP for login is 123456. Valid for 10 minutes.",
        "Thank you for shopping with us. Your order is confirmed.",
        "Class will start at 10 AM tomorrow. Please be on time."
    ] * 50  # Repeat to get more samples
    
    # Create DataFrame
    df = pd.DataFrame({
        'text': scam_messages + safe_messages,
        'label': [1] * len(scam_messages) + [0] * len(safe_messages)
    })
    
    return df


if __name__ == "__main__":
    prepare_datasets()
