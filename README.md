# BanaCommunity

## Project Setup Instructions

### Requirements

- Python 3.12 or later
- Django 4.2 or later
- Node.js and npm (Node Package Manager)

### Installation Steps

#### General Instructions

1. **Clone the repository**:
    ```sh
    git clone git@github.com:Iliess-A/BanaCommunity.git
    cd BanaCommunity
    ```
    **<span style="color:red">Ensure you create a branch with your own name</span>**
    ```sh
    git checkout -b your-branch-name
    ```

2. **Set up a virtual environment**:
    ```sh
    python3 -m venv env
    source env/bin/activate  # For Unix or macOS
    ```

3. **Install project dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Create and configure your `.env` file**:
    - Copy the sample environment file and modify it with your configuration:
      ```sh
      cp .env.example .env
      ```

#### Additional Steps for Linux

1. **Apply database migrations**:
    ```sh
    python manage.py migrate
    ```

2. **Collect static files**:
    ```sh
    python manage.py collectstatic
    ```

3. **Start Tailwind CSS**:
    ```sh
    python manage.py tailwind start
    ```

4. **Start the development server**:
    ```sh
    python manage.py runserver
    ```

#### Additional Steps for macOS

1. **Apply database migrations**:
    ```sh
    python manage.py migrate
    ```

2. **Collect static files**:
    ```sh
    python manage.py collectstatic
    ```

3. **Start Tailwind CSS**:
    ```sh
    python manage.py tailwind start
    ```

4. **Start the development server**:
    ```sh
    python manage.py runserver
    ```

### Git Branching and Workflow

- **Create a new branch**:
    ```sh
    git checkout -b your-branch-name
    ```

- **Switch to another branch**:
    ```sh
    git checkout branch-name
    ```

- **Pull the latest changes from the remote repository**:
    ```sh
    git pull origin main  # Replace 'main' with your default branch name if different
    ```

- **Merge another branch into your current branch**:
    ```sh
    git merge branch-name
    ```

- **Push your branch to the remote repository**:
    ```sh
    git push origin your-branch-name
    ```

### Notes

- Ensure that your environment variables are correctly set in the `.env` file.
- If you encounter any issues with Node.js or npm, make sure they are properly installed and configured on your system.

For any additional details, refer to the project documentation or reach out to the maintainers.

Happy coding!
