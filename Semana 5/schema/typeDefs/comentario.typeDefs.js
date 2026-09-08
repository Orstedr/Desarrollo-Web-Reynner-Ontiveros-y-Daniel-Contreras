const { gql } = require('apollo-server-express');

const comentarioTypeDefs = gql`
    type Comentario {
        id: ID!
        texto: String!
        calificacion: Int!
        usuario: Usuario
        producto: Producto
    }

    input ComentarioInput {
        texto: String!
        calificacion: Int!
        usuarioId: ID!
        productoId: ID!
    }

    extend type Usuario {
        comentarios: [Comentario]
    }

    extend type Producto {
        comentarios: [Comentario]
    }

    extend type Query {
        getComentarios: [Comentario]
        getComentariosByProducto(productoId: ID!): [Comentario]
    }

    extend type Mutation {
        addComentario(input: ComentarioInput): Comentario
        delComentario(id: ID!): Alert
    }
`;

module.exports = comentarioTypeDefs;
