from server.server import Server

def received_file(filename: str) -> None:
    print(filename)

if __name__ == "__main__":
    # from pack_loader import PackLoader
    # pl = PackLoader('../tests', '.test', 'in', 'out')
    # print(pl.load_bytes(0))
    # print(pl.load_bytes(1))
    # print(pl.load_bytes(2))
    server = Server(received_file)
    server.run()
