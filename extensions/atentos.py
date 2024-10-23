import requests

def buscar_metadados(stream_url):
    try:
        # abre a conexão com a stream
        response = requests.get(stream_url, stream=True)
        headers = response.headers

        # verifica suporte a icy (Icecast ou Shoutcast)
        if 'icy-metaint' in headers:
            metaint = int(headers['icy-metaint'])
            print("Suporte a ICY detectado.")
            
            # ignora os dados de áudio até o ponto de metadados
            audio_data = response.raw.read(metaint)
            
            # lê o tamanho dos metadados
            metadata_length = response.raw.read(1)
            if metadata_length:
                metadata_length = ord(metadata_length) * 16  # converte o byte pra inteiro
                metadata = response.raw.read(metadata_length).decode('utf-8', errors='ignore')
                
                # exibe os metadados completos
                print("Metadados ICY encontrados:")
                print(metadata)
            else:
                print("Nenhum metadado ICY encontrado.")
        else:
            print("Este stream não usa o protocolo ICY. Vamos tentar outros métodos.")

        # verificar outros headers possíveis
        if 'Content-Type' in headers:
            content_type = headers['Content-Type']
            print(f"Formato do conteúdo: {content_type}")
            
            # verificar se é áudio ou vídeo
            if 'audio' in content_type:
                print("Stream de áudio detectada.")
            elif 'video' in content_type:
                print("Stream de vídeo detectada.")
            else:
                print("Tipo de stream não identificado.")
                
        # verificar metadados diretos (ex.: alguns streams HTTP)
        if 'x-audiocast-name' in headers:
            print("Nome da stream encontrado:", headers['x-audiocast-name'])
        if 'x-audiocast-genre' in headers:
            print("Gênero da stream encontrado:", headers['x-audiocast-genre'])
        if 'x-audiocast-url' in headers:
            print("URL da stream encontrada:", headers['x-audiocast-url'])
            
        # exibe todos os headers para referência
        print("\nHeaders completos:")
        for key, value in headers.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Ocorreu um erro ao buscar metadados: {e}")

# teste com a URL de uma stream
stream_url = "https://19803.live.streamtheworld.com/NOVABRASIL_SPAAC.aac?dist=cadena-app"
buscar_metadados(stream_url)
