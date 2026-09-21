

def main():
    while True:
        try:
            user_input = input("Enter a command (or 'exit' to quit): ")
            if user_input.lower() == 'exit':
                print("Exiting the program.")
                break
            else:
                print(f"You entered: {user_input}")
        except KeyboardInterrupt:
            print("\nProgram interrupted. Exiting.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")



if __name__ == "__main__":
    main()