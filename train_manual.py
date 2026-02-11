"""
Ultra-Compatible Training Script for PRISM
Works with all Transformers versions
"""

import os
import pandas as pd
import torch
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
)
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, f1_score
from tqdm import tqdm


class ScamDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=max_length, return_tensors='pt')
        self.labels = torch.tensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = self.labels[idx]
        return item


def train_epoch(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in tqdm(dataloader, desc="Training"):
        optimizer.zero_grad()
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)


def evaluate(model, dataloader, device):
    model.eval()
    predictions = []
    true_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=-1)
            
            predictions.extend(preds.cpu().tolist())
            true_labels.extend(labels.cpu().tolist())
    
    acc = accuracy_score(true_labels, predictions)
    f1 = f1_score(true_labels, predictions, average='binary')
    
    return acc, f1


def main():
    print("🚀 Starting PRISM Model Training (Simple Version)...")
    
    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n💻 Using device: {device}")
    
    # Load data
    print("\n📥 Loading datasets...")
    train_df = pd.read_csv('data/processed/train.csv')
    test_df = pd.read_csv('data/processed/test.csv')
    print(f"   Train: {len(train_df)} samples")
    print(f"   Test: {len(test_df)} samples")
    
    # Load model and tokenizer
    print("\n🤖 Loading model...")
    model_name = "distilbert-base-multilingual-cased"
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    model = DistilBertForSequenceClassification.from_pretrained(model_name, num_labels=2)
    model.to(device)
    
    # Create datasets
    print("\n🔄 Preparing datasets...")
    train_dataset = ScamDataset(train_df['text'].tolist(), train_df['label'].tolist(), tokenizer)
    test_dataset = ScamDataset(test_df['text'].tolist(), test_df['label'].tolist(), tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=8)
    
    # Setup training
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    num_epochs = 3
    
    print(f"\n🎯 Training for {num_epochs} epochs...")
    print("=" * 60)
    print("⏰ This will take approximately 20-40 minutes")
    print("=" * 60)
    
    best_f1 = 0
    
    # Training loop
    for epoch in range(num_epochs):
        print(f"\n📚 Epoch {epoch + 1}/{num_epochs}")
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, device)
        print(f"   Training Loss: {train_loss:.4f}")
        
        # Evaluate
        acc, f1 = evaluate(model, test_loader, device)
        print(f"   Accuracy: {acc:.4f} ({acc*100:.2f}%)")
        print(f"   F1 Score: {f1:.4f}")
        
        # Save best model
        if f1 > best_f1:
            best_f1 = f1
            print(f"   ✨ New best F1! Saving model...")
            os.makedirs('models/prism-scam-detector', exist_ok=True)
            model.save_pretrained('models/prism-scam-detector')
            tokenizer.save_pretrained('models/prism-scam-detector')
    
    # Final evaluation
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print("=" * 60)
    final_acc, final_f1 = evaluate(model, test_loader, device)
    print(f"   Accuracy:  {final_acc:.4f} ({final_acc*100:.2f}%)")
    print(f"   F1 Score:  {final_f1:.4f}")
    print("=" * 60)
    
    # Save metrics
    with open('models/prism-scam-detector/metrics.txt', 'w') as f:
        f.write(f"Accuracy: {final_acc:.4f}\n")
        f.write(f"F1 Score: {final_f1:.4f}\n")
    
    print("\n✨ Training complete!")
    print("   📁 Model saved to: models/prism-scam-detector/")
    print("\n🚀 You can now run: streamlit run app.py")


if __name__ == "__main__":
    main()
