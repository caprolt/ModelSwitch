#!/usr/bin/env python3
"""
Example script to train and save models for ModelSwitch testing.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split


def create_models_directory():
    """Create the models directory structure."""
    os.makedirs("models/v1", exist_ok=True)
    os.makedirs("models/v2", exist_ok=True)
    os.makedirs("models/v3", exist_ok=True)


def train_classification_model(version: str, n_samples: int = 1000, n_features: int = 10):
    """Train a classification model."""
    print(f"Training classification model for version {version}...")
    
    # Generate synthetic data
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=8,
        n_redundant=2,
        random_state=42
    )
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"  Train accuracy: {train_score:.3f}")
    print(f"  Test accuracy: {test_score:.3f}")
    
    # Save model
    model_path = f"models/{version}/model.pkl"
    joblib.dump(model, model_path)
    print(f"  Model saved to: {model_path}")
    
    return model


def train_regression_model(version: str, n_samples: int = 1000, n_features: int = 10):
    """Train a regression model."""
    print(f"Training regression model for version {version}...")
    
    # Generate synthetic data
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=8,
        noise=0.1,
        random_state=42
    )
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"  Train R²: {train_score:.3f}")
    print(f"  Test R²: {test_score:.3f}")
    
    # Save model
    model_path = f"models/{version}/model.pkl"
    joblib.dump(model, model_path)
    print(f"  Model saved to: {model_path}")
    
    return model


def main():
    """Train example models for different versions."""
    print("Training example models for ModelSwitch...")
    
    # Create directory structure
    create_models_directory()
    
    # Train different model types for different versions
    train_classification_model("v1", n_samples=1000, n_features=10)
    train_classification_model("v2", n_samples=1500, n_features=12)
    train_regression_model("v3", n_samples=1000, n_features=8)
    
    print("\nTraining complete! Models saved to:")
    for version in ["v1", "v2", "v3"]:
        model_path = f"models/{version}/model.pkl"
        if os.path.exists(model_path):
            size = os.path.getsize(model_path) / 1024  # KB
            print(f"  {model_path} ({size:.1f} KB)")
    
    print("\nYou can now start the ModelSwitch API with:")
    print("  uvicorn app.main:app --reload")
    print("\nOr with Docker:")
    print("  docker-compose up --build")


if __name__ == "__main__":
    main() 