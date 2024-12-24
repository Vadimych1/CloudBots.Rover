from miniros.source import Server
server = Server()
server.logger.info("Running...")
server.run().join()