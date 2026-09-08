const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const { ApolloServer } = require('apollo-server-express');

const typeDefs = require('./schema/typeDefs');
const resolvers = require('./schema/resolvers');

mongoose.connect('mongodb://localhost:27017/Semana5');

async function startServer() {
    const app = express();
    app.use(cors());

    const apolloServer = new ApolloServer({ typeDefs, resolvers });
    await apolloServer.start();

    apolloServer.applyMiddleware({ app, cors: false, path: '/graphql' });

    app.listen(8090, function () {
        console.log('Servidor iniciado en http://localhost:8090' + apolloServer.graphqlPath);
    });
}

startServer();
