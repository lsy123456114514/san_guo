
#ifdef RENDERER_EXPORTS
#define RENDERER_API __declspec(dllexport)
#else
#define RENDERER_API __declspec(dllimport)
#endif

#include <stdint.h>

typedef struct {
    float r, g, b, a;
} Color4f;

typedef struct {
    float x, y, z;
} Vec3f;

typedef struct {
    float x, y, z;
    float vx, vy, vz;
    float r, g, b;
    float radius;
    int type;
} ProjectileData;

typedef struct {
    float x, y, z;
    float r, g, b;
    float size;
    int type;
} PickupData;

typedef struct {
    float x, y, z;
    float size;
    int type;
} TechBlockData;

typedef struct {
    float x, z;
    float base_height;
    float height;
    float width;
} TreeData;

typedef struct {
    float x, z;
    float width;
    float height;
    float depth;
    int type;
} StructureData;

typedef struct {
    float x, z;
    float r, g, b;
    int type;
} LocationData;

typedef struct {
    float x, y, z;
    float r, g, b;
    float animation_offset;
    int type;
} NPCData;

typedef struct {
    float x, y, z;
    float r, g, b;
    float current_health;
    float max_health;
    int type;
} EnemyData;

typedef struct {
    float x, y, z;
    float r, g, b;
    int has_weapon;
    int weapon_type;
} GeneralData;

typedef struct {
    float x, y, z;
    float r, g, b;
    float size;
    int type;
} PetData;

typedef struct {
    float x, y, z;
    float r, g, b;
    float rotation;
} PlayerData;

typedef struct {
    float x, y, z;
    float r, g, b;
    int type;
} FollowerData;

typedef struct {
    float x, y, z;
    float r, g, b, alpha;
    float size;
} ParticleData;

#ifdef __cplusplus
extern "C" {
#endif

RENDERER_API const char* get_last_error();
RENDERER_API void init_renderer(int width, int height);
RENDERER_API void render_terrain(float player_x, float player_y, float player_z, float visible_range, float block_size, float height);
RENDERER_API void render_projectiles(ProjectileData* projectiles, int count);
RENDERER_API void render_pickups(PickupData* pickups, int count);
RENDERER_API void render_tech_blocks(TechBlockData* blocks, int count);
RENDERER_API void render_trees(TreeData* trees, int count);
RENDERER_API void render_structures(StructureData* structures, int count);
RENDERER_API void render_locations(LocationData* locations, int count);
RENDERER_API void render_npcs(NPCData* npcs, int count);
RENDERER_API void render_enemies(EnemyData* enemies, int count);
RENDERER_API void render_generals(GeneralData* generals, int count);
RENDERER_API void render_pets(PetData* pets, int count);
RENDERER_API void render_player(PlayerData* player);
RENDERER_API void render_followers(FollowerData* followers, int count);
RENDERER_API void render_particles(ParticleData* particles, int count);

#ifdef __cplusplus
}
#endif
