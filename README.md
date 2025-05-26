# StarkNet Farming Automation

---

## 🚀 Description

This project is an automated system for interacting with DeFi protocols on the StarkNet network. The main features include:

- **Automated lending via ZkLend**
- **Token swaps across various DEXes**
- **Wallet and transaction management**
- **Integration with multiple DeFi protocols**

---

### 📝 Main Scripts

- **main_action.py** – Performs various DeFi actions and orchestrates complex scenarios
- **main_deploy.py** – Deploys smart contracts
- **main_deploy_new.py** – Alternative deployment script (for new versions or environments)
- **main_okx_transfer.py** – Transfers assets to/from OKX exchange
- **main_remaining_swap.py** – Performs remaining token swaps (for unprocessed wallets/tokens)
- **main_remaining_swap2.py** – Alternative/extended version of remaining swap script
- **main_swap.py** – Executes token swaps across supported DEXes
- **main_upgrade.py** – Upgrades smart contracts or protocol versions
- **main_zklending.py** – Automated lending/borrowing via ZkLend (v1)
- **main_zklending2.py** – Extended/alternative ZkLend automation (v2)
- **main_zklending3.py** – Latest/most advanced ZkLend automation (v3)

### ⚙️ Configuration

- `config.py` – Main project settings
- `constants/` – Constants and configuration files
- `abi/` – Smart contract ABIs

### 🗄️ Database

- `database/` – Modules for database operations

---

## ⚙️ Config Constants

| Name        | Description                              | Example/Default |
| ----------- | ---------------------------------------- | --------------- |
| all_proxies | List of proxies for network requests     | `[]`            |
| ETH_PRICE   | ETH price in USD (used for calculations) | `3000`          |
| max_tries   | Max retry attempts for operations        | `3`             |
| OKX_KEYS    | API keys for OKX accounts                | `{...}`         |
| pg_host     | PostgreSQL host                          | `""`            |
| pg_user     | PostgreSQL user                          | `""`            |
| pg_password | PostgreSQL password                      | `''`            |
| database    | Database name                            | `""`            |

---

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone [repository-url]
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚦 Usage

### ZkLend Operations

```bash
python main_zklending3.py
```

### Token Swaps

```bash
python main_swap.py
```

### Deployment

```bash
python main_deploy.py
```

### Other Scripts

- OKX transfers:  
  `python main_okx_transfer.py`
- Remaining swaps:  
  `python main_remaining_swap.py` or `python main_remaining_swap2.py`
- Contract upgrades:  
  `python main_upgrade.py`
- Orchestrating actions:  
  `python main_action.py`
- Previous ZkLend versions:  
  `python main_zklending.py` or `python main_zklending2.py`

---

## 📋 Requirements

- Python 3.8+
- starknet-py
- web3
- SQLAlchemy
- Other dependencies from `requirements.txt`

---

## 🔒 Security

- Store private keys securely
- Use environment variables for sensitive data
- Double-check all transactions before sending

