"""
Model Training Script for PRISM
Fine-tunes DistilBERT for scam detection
"""

import os
import pandas as pd
import numpy as np
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import torch


class ScamDataset(torch.utils.data.Dataset):
    """Custom dataset for scam detection"""
    
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    
    def __len__(self):
        return len(self.labels)


def compute_metrics(pred):
    """Compute evaluation metrics"""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='binary')
    precision = precision_score(labels, preds, average='binary')
    recall = recall_score(labels, preds, average='binary')
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


def train_model():
    """
    Train the scam detection model
    """
    print("🚀 Starting PRISM Model Training...")
    
    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n💻 Using device: {device}")
    
    if device == "cpu":
        print("⚠️  GPU not available. Training will be slower on CPU.")
    
    # Load datasets
    print("\n📥 Loading datasets...")
    train_df = pd.read_csv('data/processed/train.csv')
    test_df = pd.read_csv('data/processed/test.csv')
    
    print(f"   Train samples: {len(train_df)}")
    print(f"   Test samples: {len(test_df)}")
    
    # Load tokenizer
    print("\n🔤 Loading tokenizer...")
    model_name = "distilbert-base-multilingual-cased"
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    
    # Tokenize datasets
    print("\n🔄 Tokenizing datasets...")
    train_encodings = tokenizer(
        train_df['text'].tolist(),
        truncation=True,
        padding=True,
        max_length=128
    )
    
    test_encodings = tokenizer(
        test_df['text'].tolist(),
        truncation=True,
        padding=True,
        max_length=128
    )
    
    # Create datasets
    train_dataset = ScamDataset(train_encodings, train_df['label'].tolist())
    test_dataset = ScamDataset(test_encodings, test_df['label'].tolist())
    
    # Load model
    print("\n🤖 Loading DistilBERT model...")
    model = DistilBertForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2
    )
    
    # Training arguments
    print("\n⚙️  Setting up training configuration...")
    training_args = TrainingArguments(
        output_dir='./models/prism-scam-detector',
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=50,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        save_total_limit=2,
        warmup_steps=500,
        fp16=False,  # Disabled for compatibility
        use_cpu=True,  # Force CPU mode for stability
    )
    
    # Create trainer
    print("\n🏋️  Initializing trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Train model
    print("\n🎯 Starting training...")
    print("=" * 60)
    trainer.train()
    
    # Evaluate
    print("\n📊 Evaluating model...")
    eval_results = trainer.evaluate()
    
    print("\n" + "=" * 60)
    print("📈 FINAL RESULTS:")
    print("=" * 60)
    print(f"   Accuracy:  {eval_results['eval_accuracy']:.4f} ({eval_results['eval_accuracy']*100:.2f}%)")
    print(f"   F1 Score:  {eval_results['eval_f1']:.4f}")
    print(f"   Precision: {eval_results['eval_precision']:.4f}")
    print(f"   Recall:    {eval_results['eval_recall']:.4f}")
    print("=" * 60)
    
    # Save model and tokenizer
    print("\n💾 Saving model and tokenizer...")
    model.save_pretrained('models/prism-scam-detector')
    tokenizer.save_pretrained('models/prism-scam-detector')
    
    # Save metrics
    with open('models/prism-scam-detector/metrics.txt', 'w') as f:
        f.write(f"Accuracy: {eval_results['eval_accuracy']:.4f}\n")
        f.write(f"F1 Score: {eval_results['eval_f1']:.4f}\n")
        f.write(f"Precision: {eval_results['eval_precision']:.4f}\n")
        f.write(f"Recall: {eval_results['eval_recall']:.4f}\n")
    
    print("\n✨ Training complete!")
    print(f"   📁 Model saved to: models/prism-scam-detector/")
    
    return eval_results


if __name__ == "__main__":
    # Create directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Train model
    train_model()
