const { gql } = require('apollo-server-express');

const pedidoTypeDefs = gql`
    type DetallePedido {
        producto: Producto
        cantidad: Int!
    }

    type Pedido {
        id: ID!
        usuario: Usuario
        productos: [DetallePedido]
        estado: String!
        createdAt: String
    }

    input DetallePedidoInput {
        productoId: ID!
        cantidad: Int!
    }

    input PedidoInput {
        usuarioId: ID!
        productos: [DetallePedidoInput!]!
    }

    # Le agregamos el campo "pedidos" al tipo Usuario, que ya viene definido
    # en usuario.typeDefs.js (PR1). No lo tocamos, lo extendemos.
    extend type Usuario {
        pedidos: [Pedido]
    }

    extend type Query {
        getPedidos: [Pedido]
        getPedidoById(id: ID!): Pedido
        getPedidosByUsuario(usuarioId: ID!): [Pedido]
    }

    extend type Mutation {
        addPedido(input: PedidoInput): Pedido
        updEstadoPedido(id: ID!, estado: String!): Pedido
        delPedido(id: ID!): Alert
    }
`;

module.exports = pedidoTypeDefs;
