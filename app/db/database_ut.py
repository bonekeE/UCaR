import database
                

if __name__ == "__main__":
    try:
        db = database.Database()
        db.add_user_to_db("Vadim", 0)
    except Exception as e:
        print(f"An error occurred while initializing the database: {e}")
    
