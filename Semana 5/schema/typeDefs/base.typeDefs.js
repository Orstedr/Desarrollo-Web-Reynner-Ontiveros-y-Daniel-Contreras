const { gql } = require('apollo-server-express');

// Este archivo define el "esqueleto" del schema: los tipos Query y Mutation
// empiezan vacíos (con un campo dummy _empty) y cada entidad los "extiende"
// con sus propios campos usando `extend type Query { ... }`.
// Esto permite que cada entidad viva en su propio archivo sin pisar a las demás.
const baseTypeDefs = gql`
    type Alert {
        message: String
    }

    type Query {
        _empty: String
    }

    type Mutation {
        _empty: String
    }
`;

module.exports = baseTypeDefs;
