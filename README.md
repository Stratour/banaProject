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

2. **Set up a virtual environment**:
    ```sh
    python3 -m venv env
    source env/bin/activate  # For Unix or MacOS
    ```

3. **Install project dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Install Tailwind CSS and dependencies**:
    ```sh
    npm install
    ```

5. **Create and configure your `.env` file**:
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

3. **Start the development server**:
    ```sh
    npm run dev  # To start Tailwind CSS watch process
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
   
5. **Start the development server**:
    ```sh
    python manage.py runserver
    ```

### Notes

- Ensure that your environment variables are correctly set in the `.env` file.
- If you encounter any issues with Node.js or npm, make sure they are properly installed and configured on your system.

For any additional details, refer to the project documentation or reach out to the maintainers.

Happy coding!
