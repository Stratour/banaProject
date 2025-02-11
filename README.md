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

   **Ensure you create a branch with your own name:**

   ```sh
   git checkout -b your-branch-name
   ```

2. **Set up a virtual environment**:

   ```sh
   python3 -m venv env
   source env/bin/activate  # For Unix or macOS
   env\Scripts\activate   # For Windows
   ```

3. **Install project dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

4. **Create and configure your ****`.env`**** file**:

   - Copy the sample environment file and modify it with your configuration:
     ```sh
     cp .env.example .env
     ```

5. **Apply database migrations**:

   ```sh
   python manage.py migrate
   ```

6. **Collect static files**:

   ```sh
   python manage.py collectstatic
   ```

7. **Start the development server**:

   ```sh
   python manage.py runserver
   ```

#### Additional Steps for Tailwind CSS Setup

1. **Navigate to the Tailwind ****`static_src`**** directory**:

   ```sh
   cd theme/static_src
   ```

2. **Install Node.js dependencies**:

   ```sh
   npm install
   ```

3. **Install ****`cross-env`**** if not already installed**:

   ```sh
   npm install cross-env
   ```

4. **Start Tailwind CSS**:

   ```sh
   python manage.py tailwind start
   ```

5. **Return to the project root**:

   ```sh
   cd ../..
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
  git pull branch-name  # Be sure to be on the branch you want to pull from
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
- If you encounter any issues with Node.js or npm, ensure they are properly installed and configured on your system.
- Always test your setup after cloning the repository to ensure all steps are correctly followed.

For any additional details, refer to the project documentation or reach out to the maintainers.

Happy coding! zakaria

# banaProject
