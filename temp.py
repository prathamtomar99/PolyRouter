from pprint import pprint
import tomllib

def load_toml() -> dict:
    with open("pyproject.toml","rb") as f:
        tomllib_data = tomllib.load(f)
        return tomllib_data
    
if __name__ == "__main__":
    data: dict = load_toml()
    pprint(data)