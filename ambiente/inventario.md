# Ambiente Experimental — AV2 — Equipe Gemma

**Responsável:** Enzo Emanuel Maia Costa (202300061901)
**Ambiente de execução:** WSL2 (Ubuntu 24.04.1 LTS) sobre Windows, repositório clonado no sistema de arquivos do Linux (`~`, não em `/mnt/c`)
**Data da coleta:** 15/10/2026
**Commit do repositório na coleta:** `62f1b2ee948336fc99781877aeb0686f37b1f897` (Tue Oct 6 10:52:23 2026 -0300)

## Versões utilizadas

| Item | Versão |
|---|---|
| Sistema operacional | Ubuntu 24.04.1 LTS (Noble Numbat) |
| Kernel | 6.18.40.1-microsoft-standard-WSL2 |
| Python | 3.12.3 |
| Git | 2.43.0 |
| sysstat (vmstat/iostat) | 12.6.1-2 |
| Ollama | [preencher se a equipe decidir usá-lo no servidor, com `ollama --version`] |
| Bibliotecas do servidor | [preencher quando as dependências forem definidas] |

## Resumo do ambiente

| Item | Valor |
|---|---|
| Processador | Intel Core i5-8265U @ 1,60 GHz |
| Núcleos / threads | 4 núcleos, 8 threads (`nproc` = 8) |
| Cache da CPU | L1d 128 KiB, L1i 128 KiB, L2 1 MiB, L3 6 MiB |
| RAM visível ao WSL2 | 3,8 GiB (3.936.628 kB) |
| Swap | 1 GiB, em partição (`/dev/sdc`) |
| Disco do Linux (`/dev/sdd`) | 251 GB, 7,8 GB usados, 231 GB livres |
| Disco `C:` do Windows | 222 GB, 187 GB usados, 35 GB livres (85% de uso) |
| GPU / VRAM | Sem GPU dedicada utilizada; processamento em CPU [confirmar com `nvidia-smi`, se desejar] |

## Comandos de inventário e saídas

### Kernel

```
$ uname -a
Linux DESKTOP-BHUFF6Q 6.18.40.1-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Fri Jul 31 22:12:15 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
```

### Distribuição

```
$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.1 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
UBUNTU_CODENAME=noble
```

### Processador

```
$ lscpu   (campos principais)
Architecture:                x86_64
CPU op-mode(s):              32-bit, 64-bit
Address sizes:               39 bits physical, 48 bits virtual
Byte Order:                  Little Endian
CPU(s):                      8
On-line CPU(s) list:         0-7
Vendor ID:                   GenuineIntel
Model name:                  Intel(R) Core(TM) i5-8265U CPU @ 1.60GHz
Thread(s) per core:          2
Core(s) per socket:          4
Socket(s):                   1
Hypervisor vendor:           Microsoft
Virtualization type:         full
L1d:                         128 KiB (4 instances)
L1i:                         128 KiB (4 instances)
L2:                          1 MiB (4 instances)
L3:                          6 MiB (1 instance)
NUMA node(s):                1
```

```
$ nproc
8
```

### Memória

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       458Mi       2.8Gi       4.0Mi       642Mi       3.3Gi
Swap:          1.0Gi          0B       1.0Gi
```

```
$ head -n 20 /proc/meminfo
MemTotal:        3936628 kB
MemFree:         3507172 kB
MemAvailable:    3491340 kB
Buffers:            2076 kB
Cached:            94188 kB
SwapCached:            0 kB
Active:            33792 kB
Inactive:         115144 kB
Active(anon):       2956 kB
Inactive(anon):    53888 kB
Active(file):      30836 kB
Inactive(file):    61256 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:       1048576 kB
SwapFree:        1048576 kB
Dirty:                72 kB
Writeback:             0 kB
AnonPages:         52828 kB
Mapped:            85960 kB
```

Observação: o `free -h` e o `/proc/meminfo` foram coletados com alguns minutos de diferença. O valor de cache variou entre as duas medições (642 MiB em `free -h`, cerca de 94 MB em `Cached`), o que ilustra que o cache de páginas é dinâmico e não é um consumo fixo de memória.

### Armazenamento

```
$ lsblk
NAME MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
sda    8:0    0 722.9M  1 disk
sdb    8:16   0  96.5M  1 disk
sdc    8:32   0     1G  0 disk [SWAP]
sdd    8:48   0   256G  0 disk /mnt/wslg/distro
                                /
```

```
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
none            1.9G     0  1.9G   0% /usr/lib/modules/6.18.40.1-microsoft-standard-WSL2
none            1.9G  4.0K  1.9G   1% /mnt/wsl
drivers         222G  187G   35G  85% /usr/lib/wsl/drivers
/dev/sdd        251G  7.8G  231G   4% /
none            1.9G   36K  1.9G   1% /mnt/wslg
none            1.9G     0  1.9G   0% /usr/lib/wsl/lib
rootfs          1.9G  3.3M  1.9G   1% /init
none            1.9G  488K  1.9G   1% /run
none            1.9G     0  1.9G   0% /run/lock
none            1.9G     0  1.9G   0% /run/shm
none            1.9G   80K  1.9G   1% /mnt/wslg/versions.txt
none            1.9G   80K  1.9G   1% /mnt/wslg/doc
C:\             222G  187G   35G  85% /mnt/c
tmpfs           385M   20K  385M   1% /run/user/1000
```

```
$ swapon --show
NAME     TYPE      SIZE USED PRIO
/dev/sdc partition   1G   0B   -2
```

Os discos `sda` e `sdb` são pequenos e somente leitura (`RO=1`), internos do WSL. O disco `sdd` é o sistema de arquivos do Linux (ext4 virtual), onde o repositório e os experimentos serão executados.

### Linha de base em repouso (`vmstat` e `iostat`)

```
$ vmstat 1 5
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 0  0      0 3462404   5596 139016    0    0   945   338  172    0  0  0 100  0  0  0
 0  0      0 3462292   5596 139056    0    0     0     0  210  132  0  0 100  0  0  0
 0  0      0 3462292   5596 139056    0    0     0     0   96   60  0  0 100  0  0  0
 0  0      0 3462292   5596 139056    0    0     0     0   83   56  0  0 100  0  0  0
 0  0      0 3462292   5596 139056    0    0     0     0   93   64  0  0 100  0  0  0
```

```
$ iostat -xz 1 5   (primeiro relatório, média desde a inicialização)
Linux 6.18.40.1-microsoft-standard-WSL2 (DESKTOP-BHUFF6Q)   10/15/26   _x86_64_   (8 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           0.21    0.00    0.13    0.07    0.00   99.59

Device   r/s    rkB/s  rrqm/s  %rrqm r_await rareq-sz   w/s   wkB/s  wrqm/s  %wrqm w_await wareq-sz  %util
sda     0.75   162.17    0.51  40.52    0.63   217.29  0.00    0.00    0.00   0.00    0.00     0.00   0.04
sdb     0.09     3.51    0.12  56.65    0.68    39.19  0.00    0.00    0.00   0.00    0.00     0.00   0.00
sdc     0.10     2.40    0.00   0.00    0.16    23.84  0.00    0.00    0.00   0.00    4.50     2.00   0.00
sdd     8.07   767.89    4.16  34.03    0.65    95.16  2.21  335.70    4.50  67.05    5.32   151.86   3.14
```

Os quatro relatórios seguintes (amostras de 1 segundo) não mostraram atividade de disco, apenas CPU em 99,75% a 100% ociosa.

Leitura da linha de base: com a máquina em repouso, a CPU fica praticamente 100% ociosa, não há atividade de swap (`si` e `so` em 0), o `iowait` é próximo de zero e cerca de 3,4 GB de memória estão livres. Esses valores servem de referência para comparar com os experimentos de `mmap` (C2), concorrência (C3) e pressão de memória (C5).

## Explicação conceitual (exigida pelo enunciado, seção 5)

**Diferença entre `MemFree`, `MemAvailable`, cache e swap**

`MemFree` é a memória totalmente sem uso. `MemAvailable` estima quanta memória pode ser entregue a novos processos sem recorrer ao swap, e inclui a parte do cache de páginas e dos buffers que o kernel consegue liberar rapidamente. Em um sistema em uso, `MemAvailable` costuma ser bem maior que `MemFree`, porque grande parte da RAM "ocupada" é cache recuperável. Neste ambiente, em repouso, os dois valores ficaram próximos (3.507.172 kB e 3.491.340 kB), pois o cache estava pequeno. O swap é um espaço em disco que o kernel usa para descarregar páginas de memória pouco usadas quando a RAM aperta; é muito mais lento que a RAM, e a atividade de swap (colunas `si` e `so` do `vmstat`) é um sinal de pressão de memória.

**Por que o cache de páginas não é memória desperdiçada**

O Linux usa a RAM que está sobrando para guardar cópias de arquivos lidos do disco. Uma nova leitura do mesmo arquivo é atendida pela RAM, sem ir ao disco. Esse espaço é devolvido automaticamente e sem custo assim que outro processo precisa dele, razão pela qual `MemAvailable` o contabiliza como disponível. Neste ambiente, o valor de cache variou entre duas medições seguidas (642 MiB no `free -h` e cerca de 94 MB em `/proc/meminfo`), o que mostra que ele cresce e encolhe conforme a necessidade.

**Relação com o GenResearch-Servidor**

O corpus de documentos, o índice vetorial e os embeddings são arquivos lidos do disco várias vezes durante a ingestão e a recuperação. Na primeira leitura os dados vêm do disco; nas leituras seguintes tendem a vir do cache de páginas, o que muda o tempo medido. Por isso, nos experimentos de leitura convencional (C1) e `mmap` (C2), a primeira e a segunda execução devem ser comparadas separadamente. O `mmap` mapeia o arquivo diretamente nas páginas do cache, de modo que o acesso gera faltas de página em vez de chamadas `read()` explícitas, e o RSS passa a refletir as páginas realmente tocadas. Para datasets, índices e checkpoints grandes, o tamanho em relação à RAM disponível define se o arquivo cabe no cache ou se haverá reuso intenso de disco e, no limite, swap.

## Limitações do ambiente

- **RAM limitada:** o WSL2 enxerga 3,8 GiB. Na AV1, o mesmo tipo de ambiente chegou a registrar 6,1 GiB, então o limite do WSL2 pode variar entre execuções ou configurações. Para a AV2 vale o valor atual, e ele restringe o tamanho do corpus e do contexto no experimento de pressão de memória (C5).
- **Swap pequeno:** apenas 1 GiB, o que limita o quanto a pressão de memória pode ser estendida antes de o processo ser encerrado pelo kernel.
- **Sem GPU:** toda a execução ocorre em CPU.
- **Disco `C:` quase cheio:** 85% de uso, com 35 GB livres. Os experimentos devem evitar gerar arquivos grandes, e o repositório fica no disco do Linux (`/dev/sdd`, 231 GB livres) para que a leitura não passe pela camada de tradução do `/mnt/c`, que distorceria as medições de E/S.
- **Virtualização:** o WSL2 roda sobre um hipervisor (`Hypervisor vendor: Microsoft`). Medições de E/S e de memória refletem esse ambiente virtualizado, não um Linux em hardware nativo.
