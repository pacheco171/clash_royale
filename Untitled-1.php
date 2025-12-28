<?php
$ch = curl_init("https://www.google.com");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
if (curl_errno($ch)) {
    echo 'Erro: ' . curl_error($ch);
} else {
    echo 'Conectado com sucesso!';
}
curl_close($ch);
?>