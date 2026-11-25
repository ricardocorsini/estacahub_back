CREATE TABLE IF NOT EXISTS app.obras_exemplo (
    usuario_id bigint NOT NULL REFERENCES app.usuarios(id) ON DELETE CASCADE,
    exemplo varchar(32) NOT NULL,
    obra_id bigint NOT NULL UNIQUE REFERENCES app.obras(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, exemplo)
);
