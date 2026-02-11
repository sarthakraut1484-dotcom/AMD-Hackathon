"""
PRISM Setup Verification Script
Checks if all components are ready for hackathon demo
"""

import os
import sys

def print_status(check_name, status, message=""):
    """Print colored status message"""
    symbols = {
        'pass': '✅',
        'fail': '❌',
        'warn': '⚠️',
        'info': 'ℹ️'
    }
    print(f"{symbols.get(status, '•')} {check_name}: {message}")


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n" + "="*60)
    print("📦 CHECKING DEPENDENCIES")
    print("="*60)
    
    required_packages = [
        'streamlit',
        'transformers',
        'torch',
        'datasets',
        'sklearn',
        'pandas',
        'numpy',
        'langdetect',
        'plotly',
        'tqdm'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            print_status(package, 'pass', 'Installed')
        except ImportError:
            print_status(package, 'fail', 'NOT installed')
            all_installed = False
    
    return all_installed


def check_directory_structure():
    """Check if required directories exist"""
    print("\n" + "="*60)
    print("📁 CHECKING DIRECTORY STRUCTURE")
    print("="*60)
    
    required_dirs = [
        'src',
        'data',
        'data/raw',
        'data/processed',
        'models'
    ]
    
    all_exist = True
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print_status(directory, 'pass', 'Exists')
        else:
            print_status(directory, 'warn', 'Does not exist (will be created)')
            os.makedirs(directory, exist_ok=True)
    
    return all_exist


def check_source_files():
    """Check if all source files exist"""
    print("\n" + "="*60)
    print("📄 CHECKING SOURCE FILES")
    print("="*60)
    
    required_files = [
        'src/prepare_dataset.py',
        'src/train_model.py',
        'src/inference.py',
        'src/utils.py',
        'app.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md'
    ]
    
    all_exist = True
    
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print_status(file, 'pass', f'{size} bytes')
        else:
            print_status(file, 'fail', 'Missing!')
            all_exist = False
    
    return all_exist


def check_dataset():
    """Check if dataset has been prepared"""
    print("\n" + "="*60)
    print("📊 CHECKING DATASET")
    print("="*60)
    
    train_file = 'data/processed/train.csv'
    test_file = 'data/processed/test.csv'
    
    dataset_ready = True
    
    if os.path.exists(train_file):
        size = os.path.getsize(train_file)
        print_status('Training data', 'pass', f'{size:,} bytes')
    else:
        print_status('Training data', 'warn', 'Not prepared yet')
        print_status('Action needed', 'info', 'Run: python src/prepare_dataset.py')
        dataset_ready = False
    
    if os.path.exists(test_file):
        size = os.path.getsize(test_file)
        print_status('Test data', 'pass', f'{size:,} bytes')
    else:
        print_status('Test data', 'warn', 'Not prepared yet')
        dataset_ready = False
    
    return dataset_ready


def check_model():
    """Check if model has been trained"""
    print("\n" + "="*60)
    print("🤖 CHECKING TRAINED MODEL")
    print("="*60)
    
    model_dir = 'models/prism-scam-detector'
    
    if os.path.exists(model_dir):
        files = os.listdir(model_dir)
        if 'config.json' in files and 'pytorch_model.bin' in files:
            print_status('Model files', 'pass', f'{len(files)} files found')
            
            # Check model size
            model_file = os.path.join(model_dir, 'pytorch_model.bin')
            size = os.path.getsize(model_file) / (1024*1024)  # Convert to MB
            print_status('Model size', 'info', f'{size:.1f} MB')
            
            return True
        else:
            print_status('Model files', 'warn', 'Incomplete')
            print_status('Action needed', 'info', 'Run: python src/train_model.py')
            return False
    else:
        print_status('Model', 'warn', 'Not trained yet')
        print_status('Action needed', 'info', 'Run: python src/train_model.py')
        return False


def check_gpu():
    """Check GPU availability"""
    print("\n" + "="*60)
    print("🖥️  CHECKING GPU")
    print("="*60)
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print_status('GPU', 'pass', f'{gpu_name}')
            print_status('Training time', 'info', '~15-20 minutes')
            return True
        else:
            print_status('GPU', 'warn', 'Not available')
            print_status('Training time', 'info', '~30-45 minutes (CPU mode)')
            return False
    except:
        print_status('GPU', 'warn', 'Could not check')
        return False


def generate_report():
    """Generate comprehensive readiness report"""
    print("\n" + "="*60)
    print("🎯 PRISM READINESS REPORT")
    print("="*60)
    
    dependencies_ok = check_dependencies()
    directories_ok = check_directory_structure()
    files_ok = check_source_files()
    dataset_ok = check_dataset()
    model_ok = check_model()
    gpu_available = check_gpu()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if dependencies_ok and files_ok and dataset_ok and model_ok:
        print_status('Overall Status', 'pass', 'READY FOR DEMO! 🎉')
        print("\n🚀 You can run the app now:")
        print("   streamlit run app.py\n")
    elif dependencies_ok and files_ok and dataset_ok:
        print_status('Overall Status', 'warn', 'Almost ready - need to train model')
        print("\n📝 Next steps:")
        print("   1. python src/train_model.py")
        print("   2. streamlit run app.py\n")
    elif dependencies_ok and files_ok:
        print_status('Overall Status', 'warn', 'Need to prepare data and train model')
        print("\n📝 Next steps:")
        print("   1. python src/prepare_dataset.py")
        print("   2. python src/train_model.py")
        print("   3. streamlit run app.py\n")
    elif dependencies_ok:
        print_status('Overall Status', 'fail', 'Missing files - check project setup')
    else:
        print_status('Overall Status', 'fail', 'Missing dependencies')
        print("\n📝 First step:")
        print("   pip install -r requirements.txt\n")
    
    print("="*60)
    print("📚 For more help, check:")
    print("   • README.md - Full documentation")
    print("   • QUICKSTART.md - Quick setup guide")
    print("   • HACKATHON_GUIDE.md - Demo preparation")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🛡️  PRISM - Setup Verification\n")
    generate_report()
