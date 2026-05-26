from sklearn.linear_model import LogisticRegression


def train_fraud_model():
    # Create synthetic dataset (simulation)
    X = [
        [1000, 0, 0],
        [2000, 0, 1],
        [50000, 1, 2],
        [150000, 1, 3],
        [300000, 1, 4],
        [800, 0, 0],
        [120000, 1, 2],
        [6000, 0, 0],
        [250000, 1, 3],
        [4000, 0, 1]
    ]
    y = [0, 0, 0, 1, 1, 0, 1, 0, 1, 0]

    model = LogisticRegression()
    model.fit(X, y)

    return model
